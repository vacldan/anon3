const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");

let win;

const DEBUG = process.env.NIX_DEBUG === "1";          // otevře devtools + více logů
const VERBOSE_PY = process.env.NIX_VERBOSE === "1";   // přidá --verbose do pythonu

console.log("MAIN.JS STARTING...");

// ----------------------- PYTHON DISCOVERY (ONCE) -----------------------
function candidatePythonBins() {
  const bins = [];
  const override = process.env.PYTHON_BIN;
  if (override) bins.push(override);

  if (process.platform === "win32") {
    bins.push("py");
    bins.push("python");
    bins.push("python3");
  } else {
    bins.push("python3");
    bins.push("python");
    bins.push("py");
  }
  return bins;
}

function spawnQuick(cmd, args) {
  return new Promise((resolve) => {
    const child = spawn(cmd, args, {
      shell: false,
      windowsHide: true,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
    });

    let out = "";
    let err = "";
    child.stdout.on("data", (d) => (out += d.toString("utf8")));
    child.stderr.on("data", (d) => (err += d.toString("utf8")));

    child.on("error", () => resolve({ ok: false, out: "", err: "" }));
    child.on("close", (code) => resolve({ ok: code === 0, out, err }));
  });
}

async function discoverPythonOnce() {
  const cands = candidatePythonBins();

  for (const cmd of cands) {
    const testArgs = cmd.toLowerCase() === "py" ? ["-3", "--version"] : ["--version"];
    if (DEBUG) console.log(`[PY] probing: ${cmd} ${testArgs.join(" ")}`);

    const res = await spawnQuick(cmd, testArgs);
    const combined = (res.out + res.err).trim();

    if (res.ok && combined) {
      console.log(`[PY] Using interpreter: ${cmd} (${combined})`);
      return { cmd, isPyLauncher: cmd.toLowerCase() === "py" };
    }
  }

  console.error("[PY] Python interpreter not found. Set PYTHON_BIN env var.");
  return null;
}

let PY = null;

// ----------------------- THROTTLED PROGRESS -----------------------
function makeProgressSender() {
  let lastSentAt = 0;
  let lastMsg = "";

  return function sendProgress(msg) {
    if (!win) return;

    const clean = String(msg || "").trim();
    if (!clean) return;

    if (clean === lastMsg) return;
    lastMsg = clean;

    const now = Date.now();
    if (now - lastSentAt < 250) return; // max 4 msg/sec
    lastSentAt = now;

    win.webContents.send("progress-update", clean);
  };
}
const sendProgress = makeProgressSender();

// ----------------------- SPAWN PYTHON (FAST) -----------------------
function spawnPython(args, options, onStdout, onStderr, onClose) {
  if (!PY) {
    onStderr && onStderr(Buffer.from("Python interpreter not available."));
    onClose && onClose(1, null, "");
    return;
  }

  const pythonEnv = {
    ...process.env,
    PYTHONIOENCODING: "utf-8",
    PYTHONUTF8: "1",
    PYTHONPATH: path.dirname(args[0]), // aby importy fungovaly z python složky
  };

  const finalCmd = PY.cmd;
  const finalArgs = PY.isPyLauncher ? ["-3", ...args] : args;

  if (DEBUG) {
    console.log(`[PY] cmd: ${finalCmd}`);
    console.log(`[PY] args: ${finalArgs.join(" ")}`);
    console.log(`[PY] cwd: ${options?.cwd || process.cwd()}`);
  }

  const child = spawn(finalCmd, finalArgs, {
    ...options,
    env: pythonEnv,
    shell: false,
    windowsHide: true,
  });

  let stdoutBuf = "";

  child.stdout.on("data", (d) => {
    stdoutBuf += d.toString("utf8");
    onStdout && onStdout(d);
  });

  child.stderr.on("data", (d) => onStderr && onStderr(d));

  child.on("error", (err) => {
    onStderr && onStderr(Buffer.from(String(err.message || err)));
  });

  child.on("close", (code) => {
    onClose && onClose(code, finalCmd, stdoutBuf);
  });
}

// ----------------------- WINDOW -----------------------
function createWindow() {
  win = new BrowserWindow({
    width: 1150,
    height: 820,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    show: false,
  });

  if (DEBUG) win.webContents.openDevTools({ mode: "detach" });

  win.once("ready-to-show", () => win.show());

  win.loadFile("index.html").catch((err) => console.error("HTML load error:", err));

  win.on("closed", () => {
    win = null;
  });
}

// ----------------------- APP LIFECYCLE -----------------------
app.whenReady().then(async () => {
  PY = await discoverPythonOnce();
  if (!PY) {
    console.error("[FATAL] Python not found. Exiting.");
    app.quit();
    return;
  }
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (win === null) createWindow();
});

// ----------------------- HELPERS -----------------------
function resolvePy(scriptName) {
  const cands = [
    path.join(__dirname, "python", scriptName),
    path.join(__dirname, scriptName),
  ];
  for (const p of cands) {
    if (fs.existsSync(p)) return p;
  }
  return cands[0];
}

function parseJsonFromOutput(stdoutBuf) {
  if (!stdoutBuf) return null;
  const lines = String(stdoutBuf).trim().split(/\r?\n/);
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (line.startsWith("{") && line.endsWith("}")) {
      try { return JSON.parse(line); } catch {}
    }
  }
  return null;
}

function listAnonDocx(dir, base) {
  try {
    const prefix = `${base}_anon`.toLowerCase();
    return fs.readdirSync(dir)
      .filter((f) => f.toLowerCase().startsWith(prefix) && f.toLowerCase().endsWith(".docx"))
      .map((f) => path.join(dir, f));
  } catch {
    return [];
  }
}

function findLatest(files, sinceMs = 0) {
  if (!files.length) return null;
  try {
    const fresh = files.filter((p) => fs.statSync(p).mtimeMs >= sinceMs);
    const pool = fresh.length ? fresh : files;
    pool.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
    return pool[0];
  } catch {
    return null;
  }
}

// ----------------------- IPC -----------------------
ipcMain.handle("get-app-version", () => app.getVersion());

let dialogOpen = false;
ipcMain.handle("select-file", async () => {
  if (dialogOpen) return null;
  dialogOpen = true;

  try {
    const res = await dialog.showOpenDialog(win, {
      title: "Vyber DOCX k anonymizaci",
      properties: ["openFile"],
      filters: [
        { name: "Word dokumenty", extensions: ["docx"] },
        { name: "Všechny soubory", extensions: ["*"] },
      ],
    });

    if (res.canceled || !res.filePaths.length) return null;
    return res.filePaths[0];
  } finally {
    dialogOpen = false;
  }
});

ipcMain.handle("anonymize-document", async (evt, filePath) => {
  if (!filePath) return { success: false, error: "No file provided" };

  const dir = path.dirname(filePath);
  const base = path.basename(filePath, path.extname(filePath));

  const requestedOut = path.join(dir, `${base}_anon.docx`);
  const mapJson = path.join(dir, `${base}_map.json`);
  const mapTxt = path.join(dir, `${base}_map.txt`);

  // TURBO MODE: Use turbo CLI for maximum speed (unless verbose mode)
  const cliName = VERBOSE_PY ? "anonymize_cli.py" : "anonymize_cli_turbo.py";
  let cli = resolvePy(cliName);
  if (!fs.existsSync(cli)) {
    // Fallback to regular CLI if turbo not found
    const fallback = resolvePy("anonymize_cli.py");
    if (!fs.existsSync(fallback)) return { success: false, error: `CLI script not found: ${cli}` };
    cli = fallback;
  }

  const startedMs = Date.now();
  sendProgress("Spouštím anonymizaci...");

  return new Promise((resolve) => {
    const args = [
      cli,
      "--input", filePath,
      "--output", requestedOut,
      "--map", mapJson,
      "--map_txt", mapTxt,
    ];
    if (VERBOSE_PY) args.push("--verbose");

    spawnPython(
      args,
      { cwd: path.dirname(cli) },
      (d) => {
        const msg = d.toString("utf8");
        for (const line of msg.split("\n")) {
          const clean = line.trim();
          if (!clean) continue;
          if (clean.startsWith("{") && clean.endsWith("}")) continue;
          sendProgress(clean);
        }
      },
      (e) => {
        const msg = Buffer.isBuffer(e) ? e.toString("utf8") : String(e || "");
        if (DEBUG && msg.trim()) console.log("[PY STDERR]", msg.trim());
        if (msg.toLowerCase().includes("error")) sendProgress(`ERROR: ${msg.trim()}`);
      },
      (code, used, stdoutBuf) => {
        const elapsed = Math.round((Date.now() - startedMs) / 1000);

        let actual = null;
        const payload = parseJsonFromOutput(stdoutBuf);
        if (payload && payload.output) actual = payload.output;

        if (!actual || !fs.existsSync(actual)) {
          if (fs.existsSync(requestedOut)) actual = requestedOut;
          else {
            const inDir = listAnonDocx(dir, base);
            actual = findLatest(inDir, startedMs - 2000) || actual;
          }
        }

        if (!actual || !fs.existsSync(actual)) {
          const tmp = os.tmpdir();
          const inTmp = listAnonDocx(tmp, base);
          actual = findLatest(inTmp, startedMs - 2000) || actual;
        }

        if (actual && fs.existsSync(actual)) {
          sendProgress(`Anonymizace dokončena (${elapsed}s)`);
          resolve({
            success: true,
            outputFile: actual,
            mapJson: fs.existsSync(mapJson) ? mapJson : null,
            mapTxt: fs.existsSync(mapTxt) ? mapTxt : null,
          });
        } else {
          const error = code === 0
            ? "Anonymizace skončila bez výstupu. Zkontroluj, jestli není soubor otevřený."
            : `Python script failed with code ${code}.`;
          sendProgress(`ERROR: ${error} (${elapsed}s)`);
          resolve({ success: false, error });
        }
      }
    );
  });
});

ipcMain.handle("show-folder", async (evt, filePath) => {
  if (filePath && fs.existsSync(filePath)) shell.showItemInFolder(filePath);
});
