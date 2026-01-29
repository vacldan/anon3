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

function spawnQuick(cmd, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(cmd, args, {
      shell: false,
      windowsHide: true,
      cwd: options.cwd || undefined,
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
// ----------------------- LICENSE VALIDATION -----------------------
function getAppRootDir() {
  // V produkci: složka kde je .exe
  // Ve vývoji: __dirname
  if (app.isPackaged) {
    return path.dirname(app.getPath('exe'));
  }
  return __dirname;
}

async function checkLicense() {
  console.log("[LICENSE] Checking license...");

  const licenseScript = resolvePy("validate_license_standalone.py");
  if (!fs.existsSync(licenseScript)) {
    console.warn("[LICENSE] validate_license_standalone.py not found, skipping validation");
    return { valid: true, skipValidation: true };
  }

  // Hledej licenci ve složce s .exe (ne v resources)
  const appRoot = getAppRootDir();
  const licenseFile = path.join(appRoot, "license.lic");

  console.log(`[LICENSE] App root: ${appRoot}`);
  console.log(`[LICENSE] Looking for license at: ${licenseFile}`);
  console.log(`[LICENSE] License exists: ${fs.existsSync(licenseFile)}`);

  try {
    // Spusť script z jeho vlastního adresáře (důležité pro PyArmor)
    const scriptDir = path.dirname(licenseScript);
    const scriptName = path.basename(licenseScript);

    const args = PY.isPyLauncher
      ? ["-3", scriptName, licenseFile]
      : [scriptName, licenseFile];

    console.log(`[LICENSE] Running from: ${scriptDir}`);
    console.log(`[LICENSE] Running: ${PY.cmd} ${args.join(' ')}`);
    const result = await spawnQuick(PY.cmd, args, { cwd: scriptDir });

    console.log(`[LICENSE] Script output: ${result.out}`);
    console.log(`[LICENSE] Script stderr: ${result.err}`);

    const output = result.out.trim();

    if (output) {
      try {
        const licenseData = JSON.parse(output);
        console.log(`[LICENSE] Valid: ${licenseData.valid}, Message: ${licenseData.message}`);
        return licenseData;
      } catch (e) {
        console.error("[LICENSE] Failed to parse JSON:", e);
        return { valid: false, message: "Chyba při parsování licence", needs_activation: true };
      }
    } else {
      // Spočítej HW ID i když script selhal
      const hwResult = await spawnQuick(PY.cmd,
        PY.isPyLauncher ? ["-3", "-c", HW_ID_SCRIPT] : ["-c", HW_ID_SCRIPT]
      );
      const hwId = hwResult.out.trim() || "UNKNOWN";
      return {
        valid: false,
        message: "License check returned no output",
        needs_activation: true,
        hw_id: hwId
      };
    }
  } catch (error) {
    console.error("[LICENSE] Error checking license:", error);
    return { valid: false, message: `Chyba: ${error.message}`, needs_activation: true };
  }
}

// Inline script pro získání HW ID
const HW_ID_SCRIPT = `
import hashlib, uuid, subprocess
try:
    cpu = subprocess.check_output('wmic cpu get ProcessorId', shell=True).decode().split('\\n')[1].strip()
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)][::-1])
    disk = subprocess.check_output('wmic diskdrive get SerialNumber', shell=True).decode().split('\\n')[1].strip()
    hw = hashlib.sha256(f'{cpu}:{mac}:{disk}'.encode()).hexdigest()[:16].upper()
    print(f'{hw[:4]}-{hw[4:8]}-{hw[8:12]}-{hw[12:16]}')
except:
    print('UNKNOWN')
`.trim();

function showLicenseError(licenseData) {
  const hwId = licenseData.hw_id || "UNKNOWN";
  const message = licenseData.message || "Neplatná nebo chybějící licence";

  dialog.showMessageBoxSync({
    type: "error",
    title: "Aktivace požadována - SKRYI",
    message: "Aplikace vyžaduje platnou licenci",
    detail: `${message}\n\n` +
            `Váš Hardware ID: ${hwId}\n\n` +
            `Pro aktivaci:\n` +
            `1. Pošlete Hardware ID prodejci\n` +
            `2. Obdržíte soubor license.lic\n` +
            `3. Umístěte ho do složky s aplikací\n` +
            `4. Restartujte aplikaci`,
    buttons: ["Ukončit aplikaci"],
    defaultId: 0
  });

  console.log("[LICENSE] Application closing - no valid license");
  app.quit();
  return false;
}

app.whenReady().then(async () => {
  PY = await discoverPythonOnce();
  if (!PY) {
    console.error("[FATAL] Python not found. Exiting.");
    app.quit();
    return;
  }

  // Check license before creating window
  const licenseData = await checkLicense();

  if (!licenseData.valid && !licenseData.skipValidation) {
    const continueAnyway = showLicenseError(licenseData);
    if (!continueAnyway) {
      return; // User chose to exit
    }
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
  // V zabaleném Electron app jsou Python soubory v app.asar.unpacked, ne v app.asar
  const unpackedDir = __dirname.replace('app.asar', 'app.asar.unpacked');

  const cands = [
    // Nejdřív hledej v unpacked složce (pro produkci)
    path.join(unpackedDir, scriptName),
    path.join(unpackedDir, "python", scriptName),
    // Pak v __dirname (pro vývoj)
    path.join(__dirname, scriptName),
    path.join(__dirname, "python", scriptName),
  ];

  for (const p of cands) {
    if (fs.existsSync(p)) {
      console.log(`[RESOLVE] Found ${scriptName} at: ${p}`);
      return p;
    }
  }

  console.warn(`[RESOLVE] ${scriptName} not found in any location`);
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

        // Try to parse JSON output from CLI first
        const payload = parseJsonFromOutput(stdoutBuf);

        // Use paths from CLI output if available
        let actual = null;
        let actualMapJson = null;
        let actualMapTxt = null;

        if (payload && payload.output) {
          actual = payload.output;
          actualMapJson = payload.map_json || null;
          actualMapTxt = payload.map_txt || null;
        }

        // Fallback: try to find files if CLI didn't return paths
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

        // Fallback for maps if not in JSON output
        if (!actualMapJson || !fs.existsSync(actualMapJson)) {
          actualMapJson = fs.existsSync(mapJson) ? mapJson : null;
        }
        if (!actualMapTxt || !fs.existsSync(actualMapTxt)) {
          actualMapTxt = fs.existsSync(mapTxt) ? mapTxt : null;
        }

        if (actual && fs.existsSync(actual)) {
          sendProgress(`Anonymizace dokončena (${elapsed}s)`);
          resolve({
            success: true,
            outputFile: actual,
            mapJson: actualMapJson,
            mapTxt: actualMapTxt,
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

ipcMain.handle("select-anon-file", async () => {
  if (dialogOpen) return null;
  dialogOpen = true;

  try {
    const res = await dialog.showOpenDialog(win, {
      title: "Vyber anonymizovaný DOCX k deanonymizaci",
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

ipcMain.handle("select-map-file", async () => {
  if (dialogOpen) return null;
  dialogOpen = true;

  try {
    const res = await dialog.showOpenDialog(win, {
      title: "Vyber JSON mapu",
      properties: ["openFile"],
      filters: [
        { name: "JSON soubory", extensions: ["json"] },
        { name: "Všechny soubory", extensions: ["*"] },
      ],
    });

    if (res.canceled || !res.filePaths.length) return null;
    return res.filePaths[0];
  } finally {
    dialogOpen = false;
  }
});

ipcMain.handle("deanonymize-document", async (evt, anonFile, mapFile) => {
  if (!anonFile || !mapFile) return { success: false, error: "Chybí vstupní soubory" };

  const dir = path.dirname(anonFile);
  const base = path.basename(anonFile, path.extname(anonFile));

  // Remove _anon suffix if present to get the original base name
  const cleanBase = base.endsWith("_anon") ? base.slice(0, -5) : base;
  const requestedOut = path.join(dir, `${cleanBase}_deanon.docx`);

  const cli = resolvePy("deanonymizator_lokal.py");
  if (!fs.existsSync(cli)) {
    return { success: false, error: `Deanonymizátor nenalezen: ${cli}` };
  }

  const startedMs = Date.now();
  sendProgress("Spouštím deanonymizaci...");

  return new Promise((resolve) => {
    const args = [
      cli,
      "--input", anonFile,
      "--map", mapFile,
      "--output", requestedOut,
    ];

    let stderrBuffer = "";

    spawnPython(
      args,
      { cwd: path.dirname(cli) },
      (d) => {
        const msg = d.toString("utf8");
        for (const line of msg.split("\n")) {
          const clean = line.trim();
          if (!clean) continue;
          sendProgress(clean);
        }
      },
      (e) => {
        const msg = Buffer.isBuffer(e) ? e.toString("utf8") : String(e || "");
        if (msg.trim()) {
          stderrBuffer += msg;
          if (DEBUG) console.log("[PY STDERR]", msg.trim());
          // Zobraz všechny chybové zprávy
          if (msg.toLowerCase().includes("error") || msg.toLowerCase().includes("chyba") ||
              msg.includes("✗") || msg.includes("CRITICAL") || msg.includes("KRITICK")) {
            sendProgress(msg.trim());
          }
        }
      },
      (code, used, stdoutBuf) => {
        const elapsed = Math.round((Date.now() - startedMs) / 1000);

        if (DEBUG) {
          console.log(`[DEANON] Exit code: ${code}`);
          console.log(`[DEANON] Output file exists: ${fs.existsSync(requestedOut)}`);
          console.log(`[DEANON] Output path: ${requestedOut}`);
          console.log(`[DEANON] Stderr buffer length: ${stderrBuffer.length}`);
        }

        if (code === 0 && fs.existsSync(requestedOut)) {
          // DŮLEŽITÉ: Použij win.webContents.send přímo pro finální zprávu
          // aby se nepotlačila throttlingem
          if (win) {
            win.webContents.send("progress-update", `Deanonymizace dokončena (${elapsed}s)`);
          }
          resolve({
            success: true,
            outputFile: requestedOut,
          });
        } else {
          let error = code === 0
            ? "Deanonymizace skončila bez výstupu."
            : `Deanonymizace selhala s kódem ${code}.`;

          // Pokud máme stderr výstup, přidej ho do chybové zprávy
          if (stderrBuffer.trim()) {
            error += `\n\nChybový výstup:\n${stderrBuffer.trim()}`;
          }

          // DŮLEŽITÉ: Použij win.webContents.send přímo pro chybovou zprávu
          if (win) {
            win.webContents.send("progress-update", `ERROR: ${error.split('\n')[0]} (${elapsed}s)`);
            // Pokud je stderr, pošli ho jako další zprávu
            if (stderrBuffer.trim()) {
              const stderrLines = stderrBuffer.trim().split('\n').slice(0, 10); // max 10 řádků
              stderrLines.forEach(line => {
                if (line.trim()) {
                  win.webContents.send("progress-update", line.trim());
                }
              });
            }
          }
          resolve({ success: false, error });
        }
      }
    );
  });
});

// PDF to DOCX conversion handler
ipcMain.handle("convert-pdf-to-docx", async (evt, pdfPath) => {
  if (!pdfPath) return { success: false, error: "No PDF file provided" };

  const dir = path.dirname(pdfPath);
  const base = path.basename(pdfPath, path.extname(pdfPath));
  const expectedDocx = path.join(dir, `${base}.docx`);

  const cli = resolvePy("pdf2docx_cli.py");
  if (!fs.existsSync(cli)) {
    return { success: false, error: `PDF converter script not found: ${cli}` };
  }

  const startedMs = Date.now();
  sendProgress("Spouštím PDF → DOCX konverzi...");

  return new Promise((resolve) => {
    const args = [cli, pdfPath];

    spawnPython(
      args,
      {
        cwd: path.dirname(cli),
        env: {
          ...process.env,
          PYTHONIOENCODING: "utf-8",
          PYTHONUTF8: "1",
          PYTHONUNBUFFERED: "1",
          NO_PAUSE: "1",
        }
      },
      (d) => {
        const msg = d.toString("utf8");
        for (const line of msg.split("\n")) {
          const clean = line.trim();
          if (!clean) continue;
          // Skip technical info but allow success messages
          if (clean.includes("[INFO]")) continue;
          if (clean.includes("====") && !clean.includes("✅") && !clean.includes("VÝSLEDEK")) continue;
          sendProgress(clean);
        }
      },
      (e) => {
        const msg = Buffer.isBuffer(e) ? e.toString("utf8") : String(e || "");
        if (DEBUG && msg.trim()) console.log("[PDF2DOCX STDERR]", msg.trim());
        if (msg.toLowerCase().includes("error")) sendProgress(`ERROR: ${msg.trim()}`);
      },
      (code) => {
        const elapsed = Math.round((Date.now() - startedMs) / 1000);

        if (code === 0 && fs.existsSync(expectedDocx)) {
          sendProgress(`✅ PDF převedeno úspěšně (${elapsed}s)`);
          resolve({
            success: true,
            outputFile: expectedDocx,
          });
        } else {
          const error = code === 0
            ? "Výstupní DOCX soubor nebyl vytvořen"
            : `Python skript skončil s chybou (exit code ${code})`;
          sendProgress(`ERROR: ${error}`);
          resolve({ success: false, error });
        }
      }
    );
  });
});

// Handler for selecting PDF file
ipcMain.handle("select-pdf-file", async () => {
  const result = await dialog.showOpenDialog(win, {
    title: "Vyberte PDF soubor",
    filters: [{ name: "PDF soubory", extensions: ["pdf"] }],
    properties: ["openFile"],
  });
  if (result.canceled || !result.filePaths.length) return null;
  return result.filePaths[0];
});

// License info handler
ipcMain.handle("get-license-info", async () => {
  const licenseScript = resolvePy("validate_license_standalone.py");
  if (!fs.existsSync(licenseScript)) {
    return { valid: false, message: "License validation not available" };
  }

  const appRoot = getAppRootDir();
  const licenseFile = path.join(appRoot, "license.lic");
  const scriptDir = path.dirname(licenseScript);
  const scriptName = path.basename(licenseScript);
  const args = PY.isPyLauncher ? ["-3", scriptName, licenseFile] : [scriptName, licenseFile];

  try {
    const result = await spawnQuick(PY.cmd, args, { cwd: scriptDir });
    const output = result.out.trim();

    if (output) {
      return JSON.parse(output);
    }
    return { valid: false, message: "No output from license check" };
  } catch (error) {
    console.error("[LICENSE-INFO] Error:", error);
    return { valid: false, message: `Error: ${error.message}` };
  }
});
