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

function findLicenseFile() {
  // Hledej license.lic ve více lokacích
  const appRoot = getAppRootDir();
  const userData = app.getPath('userData');
  const unpackedDir = __dirname.replace('app.asar', 'app.asar.unpacked');

  const candidates = [
    path.join(appRoot, "license.lic"),          // Složka s .exe (produkce) nebo __dirname (vývoj)
    path.join(userData, "license.lic"),          // AppData - přežije reinstalace
    path.join(unpackedDir, "license.lic"),       // resources/app.asar.unpacked
    path.join(__dirname, "license.lic"),         // Uvnitř app.asar (fallback)
  ];

  console.log("[LICENSE] Searching for license.lic in:");
  for (const c of candidates) {
    const exists = fs.existsSync(c);
    console.log(`[LICENSE]   ${exists ? "FOUND" : "     "} ${c}`);
    if (exists) return c;
  }

  console.log("[LICENSE] license.lic not found in any location");
  return null;
}

function copyLicenseToUserData(sourcePath) {
  // Zkopíruj licenci do AppData, aby přežila reinstalace
  try {
    const userData = app.getPath('userData');
    const targetPath = path.join(userData, "license.lic");
    if (sourcePath !== targetPath) {
      if (!fs.existsSync(userData)) {
        fs.mkdirSync(userData, { recursive: true });
      }
      fs.copyFileSync(sourcePath, targetPath);
      console.log(`[LICENSE] License copied to AppData: ${targetPath}`);
    }
  } catch (e) {
    console.warn(`[LICENSE] Could not copy license to AppData: ${e.message}`);
  }
}

async function checkLicense() {
  console.log("[LICENSE] Checking license...");

  const script = resolveScript("validate_license_standalone.py");
  if (!fs.existsSync(script.path)) {
    console.warn("[LICENSE] License validator not found, skipping validation");
    return { valid: true, skipValidation: true };
  }

  // Hledej licenci ve více složkách
  const licenseFile = findLicenseFile();
  const appRoot = getAppRootDir();

  console.log(`[LICENSE] App root: ${appRoot}`);
  console.log(`[LICENSE] License file: ${licenseFile || "NOT FOUND"}`);
  console.log(`[LICENSE] Using compiled exe: ${script.isExe}`);

  if (!licenseFile) {
    // Licence nenalezena - zjisti HW ID pro aktivaci
    let hwId = "UNKNOWN";
    try {
      const hwResult = await spawnQuick(PY.cmd,
        PY.isPyLauncher ? ["-3", "-c", HW_ID_SCRIPT] : ["-c", HW_ID_SCRIPT]
      );
      hwId = hwResult.out.trim() || "UNKNOWN";
    } catch (e) { /* ignore */ }

    return {
      valid: false,
      message: "Licenční soubor nenalezen",
      needs_activation: true,
      hw_id: hwId,
      search_paths: [
        path.join(appRoot, "license.lic"),
        path.join(app.getPath('userData'), "license.lic"),
      ]
    };
  }

  try {
    const scriptDir = path.dirname(script.path);
    let result;

    if (script.isExe) {
      // Nuitka compiled .exe - run directly
      console.log(`[LICENSE] Running exe: ${script.path} ${licenseFile}`);
      result = await spawnQuick(script.path, [licenseFile], { cwd: scriptDir });
    } else {
      // Python script - run via interpreter
      const scriptName = path.basename(script.path);
      const args = PY.isPyLauncher
        ? ["-3", scriptName, licenseFile]
        : [scriptName, licenseFile];
      console.log(`[LICENSE] Running: ${PY.cmd} ${args.join(' ')}`);
      result = await spawnQuick(PY.cmd, args, { cwd: scriptDir });
    }

    console.log(`[LICENSE] Script ok: ${result.ok}`);
    console.log(`[LICENSE] Script output: ${result.out}`);
    if (result.err) console.log(`[LICENSE] Script stderr: ${result.err}`);

    const output = result.out.trim();

    if (output) {
      try {
        const licenseData = JSON.parse(output);
        console.log(`[LICENSE] Valid: ${licenseData.valid}, Message: ${licenseData.message}`);

        // Pokud je licence platná, zkopíruj ji do AppData (přežije reinstalace)
        if (licenseData.valid) {
          copyLicenseToUserData(licenseFile);
        }

        return licenseData;
      } catch (e) {
        console.error("[LICENSE] Failed to parse JSON:", e);
        return { valid: false, message: "Chyba při parsování licence", needs_activation: true };
      }
    } else {
      // .exe selhal bez výstupu - možná antivirus blokuje, nebo WMIC chybí
      console.error("[LICENSE] Validator produced no output! Possible causes: antivirus blocking .exe, missing wmic, or crash");
      if (result.err) console.error(`[LICENSE] Stderr: ${result.err}`);

      // Zkus fallback: spusť Python script přímo pokud .exe selhalo
      if (script.isExe && PY && PY.cmd) {
        console.log("[LICENSE] Trying Python fallback...");
        const pyScript = path.join(scriptDir, "validate_license_standalone.py");
        const pyScriptAlt = path.join(__dirname, "validate_license_standalone.py");
        const pyPath = fs.existsSync(pyScript) ? pyScript : (fs.existsSync(pyScriptAlt) ? pyScriptAlt : null);

        if (pyPath) {
          const pyArgs = PY.isPyLauncher
            ? ["-3", pyPath, licenseFile]
            : [pyPath, licenseFile];
          const pyResult = await spawnQuick(PY.cmd, pyArgs, { cwd: path.dirname(pyPath) });
          const pyOutput = pyResult.out.trim();
          if (pyOutput) {
            try {
              const licenseData = JSON.parse(pyOutput);
              console.log(`[LICENSE] Python fallback succeeded: ${licenseData.valid}`);
              if (licenseData.valid) copyLicenseToUserData(licenseFile);
              return licenseData;
            } catch (e) { /* fall through */ }
          }
        }
      }

      // Spočítej HW ID i když script selhal
      const hwResult = await spawnQuick(PY.cmd,
        PY.isPyLauncher ? ["-3", "-c", HW_ID_SCRIPT] : ["-c", HW_ID_SCRIPT]
      );
      const hwId = hwResult.out.trim() || "UNKNOWN";
      return {
        valid: false,
        message: "Validátor licence nevrátil výstup. Možné příčiny: antivirus blokuje .exe, chybí wmic, nebo pád programu." +
                 (result.err ? ` Chyba: ${result.err.substring(0, 200)}` : ""),
        needs_activation: true,
        hw_id: hwId
      };
    }
  } catch (error) {
    console.error("[LICENSE] Error checking license:", error);
    return { valid: false, message: `Chyba: ${error.message}`, needs_activation: true };
  }
}

// Inline script pro získání HW ID (s PowerShell fallbackem pro Windows 11 bez WMIC)
const HW_ID_SCRIPT = `
import hashlib, uuid, subprocess, platform

def get_cpu():
    try:
        r = subprocess.check_output('wmic cpu get ProcessorId', shell=True, stderr=subprocess.DEVNULL)
        v = r.decode().split('\\n')[1].strip()
        if v and v != 'ProcessorId': return v
    except: pass
    try:
        r = subprocess.check_output(['powershell', '-NoProfile', '-Command',
            'Get-CimInstance -ClassName Win32_Processor | Select-Object -ExpandProperty ProcessorId'],
            shell=False, stderr=subprocess.DEVNULL)
        v = r.decode().strip()
        if v: return v
    except: pass
    return platform.processor()

def get_disk():
    try:
        r = subprocess.check_output('wmic diskdrive get SerialNumber', shell=True, stderr=subprocess.DEVNULL)
        lines = [l.strip() for l in r.decode().split('\\n') if l.strip() and l.strip() != 'SerialNumber']
        if lines: return lines[0]
    except: pass
    try:
        r = subprocess.check_output(['powershell', '-NoProfile', '-Command',
            '(Get-CimInstance -ClassName Win32_DiskDrive | Select-Object -First 1).SerialNumber'],
            shell=False, stderr=subprocess.DEVNULL)
        v = r.decode().strip()
        if v: return v
    except: pass
    return 'UNKNOWN'

try:
    cpu = get_cpu()
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)][::-1])
    disk = get_disk()
    hw = hashlib.sha256(f'{cpu}:{mac}:{disk}'.encode()).hexdigest()[:16].upper()
    print(f'{hw[:4]}-{hw[4:8]}-{hw[8:12]}-{hw[12:16]}')
except:
    print('UNKNOWN')
`.trim();

function showLicenseError(licenseData) {
  const hwId = licenseData.hw_id || "UNKNOWN";
  const message = licenseData.message || "Neplatná nebo chybějící licence";
  const appRoot = getAppRootDir();
  const userData = app.getPath('userData');

  // Ukáž přesné cesty kam umístit licenci
  const paths = [
    appRoot,
    userData,
  ];
  const pathsList = paths.map(p => `  • ${p}`).join('\n');

  dialog.showMessageBoxSync({
    type: "error",
    title: "Aktivace požadována - SKRYI",
    message: "Aplikace vyžaduje platnou licenci",
    detail: `${message}\n\n` +
            `Váš Hardware ID: ${hwId}\n\n` +
            `Pro aktivaci:\n` +
            `1. Pošlete Hardware ID prodejci\n` +
            `2. Obdržíte soubor license.lic\n` +
            `3. Umístěte ho do jedné z těchto složek:\n${pathsList}\n` +
            `4. Restartujte aplikaci`,
    buttons: ["Ukončit aplikaci"],
    defaultId: 0
  });

  console.log("[LICENSE] Application closing - no valid license");
  console.log(`[LICENSE] Place license.lic in one of: ${paths.join(' OR ')}`);
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
// Resolve script - prefers .exe (Nuitka compiled), falls back to .py
function resolveScript(baseName) {
  const unpackedDir = __dirname.replace('app.asar', 'app.asar.unpacked');
  const exeName = baseName.replace('.py', '.exe');
  const pyName = baseName;

  // First look for compiled .exe (Nuitka)
  const exeCands = [
    path.join(unpackedDir, exeName),
    path.join(__dirname, exeName),
  ];

  for (const p of exeCands) {
    if (fs.existsSync(p)) {
      console.log(`[RESOLVE] Found compiled ${exeName} at: ${p}`);
      return { path: p, isExe: true };
    }
  }

  // Fallback to .py script
  const pyCands = [
    path.join(unpackedDir, pyName),
    path.join(unpackedDir, "python", pyName),
    path.join(__dirname, pyName),
    path.join(__dirname, "python", pyName),
  ];

  for (const p of pyCands) {
    if (fs.existsSync(p)) {
      console.log(`[RESOLVE] Found script ${pyName} at: ${p}`);
      return { path: p, isExe: false };
    }
  }

  console.warn(`[RESOLVE] ${baseName} not found in any location`);
  return { path: pyCands[0], isExe: false };
}

// Legacy function for compatibility
function resolvePy(scriptName) {
  const result = resolveScript(scriptName);
  return result.path;
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
  let cliScript = resolveScript(cliName);
  if (!fs.existsSync(cliScript.path)) {
    // Fallback to regular CLI if turbo not found
    cliScript = resolveScript("anonymize_cli.py");
    if (!fs.existsSync(cliScript.path)) return { success: false, error: `CLI script not found: ${cliScript.path}` };
  }

  const startedMs = Date.now();
  sendProgress("Spouštím anonymizaci...");

  // Build CLI arguments
  const cliArgs = [
    "--input", filePath,
    "--output", requestedOut,
    "--map", mapJson,
    "--map_txt", mapTxt,
  ];
  if (VERBOSE_PY) cliArgs.push("--verbose");

  const cwd = path.dirname(cliScript.path);

  // If it's a compiled EXE, run directly; otherwise use Python interpreter
  if (cliScript.isExe) {
    console.log(`[ANON] Running EXE directly: ${cliScript.path}`);
    return new Promise((resolve) => {
      const child = spawn(cliScript.path, cliArgs, {
        cwd,
        env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" },
        shell: false,
        windowsHide: true,
      });

      let stdoutBuf = "";

      child.stdout.on("data", (d) => {
        const msg = d.toString("utf8");
        stdoutBuf += msg;
        for (const line of msg.split("\n")) {
          const clean = line.trim();
          if (!clean) continue;
          if (clean.startsWith("{") && clean.endsWith("}")) continue;
          sendProgress(clean);
        }
      });

      child.stderr.on("data", (e) => {
        const msg = Buffer.isBuffer(e) ? e.toString("utf8") : String(e || "");
        if (DEBUG && msg.trim()) console.log("[PY STDERR]", msg.trim());
        if (msg.toLowerCase().includes("error")) sendProgress(`ERROR: ${msg.trim()}`);
      });

      child.on("error", (err) => {
        console.error("[ANON] Spawn error:", err);
        resolve({ success: false, error: err.message });
      });

      child.on("close", (code) => {
        handleAnonymizeResult(code, stdoutBuf, startedMs, dir, base, requestedOut, mapJson, mapTxt, resolve);
      });
    });
  }

  // Fallback: Python script mode
  return new Promise((resolve) => {
    const args = [cliScript.path, ...cliArgs];

    spawnPython(
      args,
      { cwd },
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
        handleAnonymizeResult(code, stdoutBuf, startedMs, dir, base, requestedOut, mapJson, mapTxt, resolve);
      }
    );
  });
});

// Helper function for anonymization result handling
function handleAnonymizeResult(code, stdoutBuf, startedMs, dir, base, requestedOut, mapJson, mapTxt, resolve) {
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
    logStat("anonymize", { persons: payload ? (payload.persons_found || 0) : 0 });
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

  const script = resolveScript("deanonymizator_lokal.py");
  if (!fs.existsSync(script.path)) {
    return { success: false, error: `Deanonymizator nenalezen: ${script.path}` };
  }

  const startedMs = Date.now();
  sendProgress("Spoustim deanonymizaci...");

  return new Promise((resolve) => {
    let stderrBuffer = "";
    let stdoutBuffer = "";
    let child;

    const cliArgs = [
      "--input", anonFile,
      "--map", mapFile,
      "--output", requestedOut,
    ];

    // Spawn directly for exe, or via Python for .py
    if (script.isExe) {
      child = spawn(script.path, cliArgs, {
        cwd: path.dirname(script.path),
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
        shell: false,
        windowsHide: true,
      });
    } else {
      const pythonEnv = {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
        PYTHONPATH: path.dirname(script.path),
      };
      const pyArgs = PY.isPyLauncher ? ["-3", script.path, ...cliArgs] : [script.path, ...cliArgs];
      child = spawn(PY.cmd, pyArgs, {
        cwd: path.dirname(script.path),
        env: pythonEnv,
        shell: false,
        windowsHide: true,
      });
    }

    child.stdout.on("data", (d) => {
      const msg = d.toString("utf8");
      stdoutBuffer += msg;
      for (const line of msg.split("\n")) {
        const clean = line.trim();
        if (!clean) continue;
        sendProgress(clean);
      }
    });

    child.stderr.on("data", (e) => {
      const msg = Buffer.isBuffer(e) ? e.toString("utf8") : String(e || "");
      if (msg.trim()) {
        stderrBuffer += msg;
        if (DEBUG) console.log("[DEANON STDERR]", msg.trim());
        if (msg.toLowerCase().includes("error") || msg.toLowerCase().includes("chyba")) {
          sendProgress(msg.trim());
        }
      }
    });

    child.on("close", (code) => {
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
          logStat("deanonymize");
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
    });
  });
});

// PDF to DOCX conversion handler
ipcMain.handle("convert-pdf-to-docx", async (evt, pdfPath) => {
  if (!pdfPath) return { success: false, error: "No PDF file provided" };

  const dir = path.dirname(pdfPath);
  const base = path.basename(pdfPath, path.extname(pdfPath));
  const expectedDocx = path.join(dir, `${base}.docx`);

  const script = resolveScript("pdf2docx_cli.py");
  if (!fs.existsSync(script.path)) {
    return { success: false, error: `PDF converter script not found: ${script.path}` };
  }

  const startedMs = Date.now();
  sendProgress("Spoustim PDF -> DOCX konverzi...");

  return new Promise((resolve) => {
    let child;
    let stderrBuf = "";
    let lastStdoutLines = [];
    const cliArgs = [pdfPath];

    // Spawn directly for exe, or via Python for .py
    if (script.isExe) {
      child = spawn(script.path, cliArgs, {
        cwd: path.dirname(script.path),
        env: {
          ...process.env,
          PYTHONIOENCODING: "utf-8",
          NO_PAUSE: "1",
        },
        shell: false,
        windowsHide: true,
      });
    } else {
      const pythonEnv = {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
        PYTHONUNBUFFERED: "1",
        NO_PAUSE: "1",
      };
      const pyArgs = PY.isPyLauncher ? ["-3", script.path, ...cliArgs] : [script.path, ...cliArgs];
      child = spawn(PY.cmd, pyArgs, {
        cwd: path.dirname(script.path),
        env: pythonEnv,
        shell: false,
        windowsHide: true,
      });
    }

    child.stdout.on("data", (d) => {
      const msg = d.toString("utf8");
      for (const line of msg.split("\n")) {
        const clean = line.trim();
        if (!clean) continue;
        // Keep last stdout lines for error diagnostics
        lastStdoutLines.push(clean);
        if (lastStdoutLines.length > 20) lastStdoutLines.shift();
        // Skip technical info but allow success messages
        if (clean.includes("[INFO]")) continue;
        if (clean.includes("====") && !clean.includes("[OK]") && !clean.includes("VYSLEDEK")) continue;
        sendProgress(clean);
      }
    });

    child.stderr.on("data", (e) => {
      const msg = Buffer.isBuffer(e) ? e.toString("utf8") : String(e || "");
      stderrBuf += msg;
      if (msg.trim()) console.log("[PDF2DOCX STDERR]", msg.trim());
      if (msg.toLowerCase().includes("error")) sendProgress(`ERROR: ${msg.trim()}`);
    });

    child.on("close", (code) => {
      const elapsed = Math.round((Date.now() - startedMs) / 1000);

      if (code === 0 && fs.existsSync(expectedDocx)) {
        sendProgress(`[OK] PDF prevedeno uspesne (${elapsed}s)`);
        // Detect if OCR was used from stdout
        const usedOcr = lastStdoutLines.some(l => l.includes("OCR") || l.includes("SKENOVANE"));
        logStat("pdf", { ocr: usedOcr });
        resolve({
          success: true,
          outputFile: expectedDocx,
        });
      } else {
        // Build detailed error message
        let error = code === 0
          ? "Vystupni DOCX soubor nebyl vytvoren"
          : `Skript skoncil s chybou (exit code ${code})`;

        // Include stderr and last stdout lines for diagnostics
        const details = [];
        if (stderrBuf.trim()) details.push(stderrBuf.trim().slice(-500));
        const errorLines = lastStdoutLines.filter(l => l.includes("ERROR") || l.includes("selhalo") || l.includes("neni"));
        if (errorLines.length) details.push(errorLines.join("; "));
        if (details.length) error += " | " + details.join(" | ");

        sendProgress(`ERROR: ${error}`);
        resolve({ success: false, error });
      }
    });
  });
});

// Handler for selecting PDF file
// ----------------------- STATS -----------------------
const STATS_FILE = path.join(__dirname, "skryi_stats.json");

function readStats() {
  try {
    if (fs.existsSync(STATS_FILE)) {
      return JSON.parse(fs.readFileSync(STATS_FILE, "utf8"));
    }
  } catch (e) { /* ignore */ }
  return {
    total_anonymized: 0, total_deanonymized: 0,
    total_pdf_converted: 0, total_pdf_ocr: 0,
    total_persons_found: 0, monthly: {},
  };
}

function saveStats(stats) {
  try {
    fs.writeFileSync(STATS_FILE, JSON.stringify(stats, null, 2), "utf8");
  } catch (e) { console.log("[STATS] Write error:", e.message); }
}

function logStat(type, extra = {}) {
  const stats = readStats();
  const now = new Date();
  const month = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
  if (!stats.monthly) stats.monthly = {};
  if (!stats.monthly[month]) stats.monthly[month] = {};
  const m = stats.monthly[month];

  if (type === "anonymize") {
    stats.total_anonymized = (stats.total_anonymized || 0) + 1;
    stats.total_persons_found = (stats.total_persons_found || 0) + (extra.persons || 0);
    m.anonymized = (m.anonymized || 0) + 1;
    m.persons_found = (m.persons_found || 0) + (extra.persons || 0);
  } else if (type === "deanonymize") {
    stats.total_deanonymized = (stats.total_deanonymized || 0) + 1;
    m.deanonymized = (m.deanonymized || 0) + 1;
  } else if (type === "pdf") {
    stats.total_pdf_converted = (stats.total_pdf_converted || 0) + 1;
    m.pdf_converted = (m.pdf_converted || 0) + 1;
    if (extra.ocr) {
      stats.total_pdf_ocr = (stats.total_pdf_ocr || 0) + 1;
      m.pdf_ocr = (m.pdf_ocr || 0) + 1;
    }
  }
  saveStats(stats);
}

ipcMain.handle("get-stats", async () => readStats());

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
  const script = resolveScript("validate_license_standalone.py");
  if (!fs.existsSync(script.path)) {
    return { valid: false, message: "License validation not available" };
  }

  const appRoot = getAppRootDir();
  const licenseFile = path.join(appRoot, "license.lic");
  const scriptDir = path.dirname(script.path);

  try {
    let result;
    if (script.isExe) {
      result = await spawnQuick(script.path, [licenseFile], { cwd: scriptDir });
    } else {
      const scriptName = path.basename(script.path);
      const args = PY.isPyLauncher ? ["-3", scriptName, licenseFile] : [scriptName, licenseFile];
      result = await spawnQuick(PY.cmd, args, { cwd: scriptDir });
    }

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

// ----------------------- FOLDER MODE HANDLERS -----------------------
// Get SKRYI folders path
function getSkryiFolders() {
  const documents = app.getPath('documents');
  const baseFolder = path.join(documents, 'SKRYI');
  return {
    base: baseFolder,
    // 01_ANONYMIZACE
    anonFolder: path.join(baseFolder, '01_ANONYMIZACE'),
    anonIn: path.join(baseFolder, '01_ANONYMIZACE', 'IN'),
    anonOut: path.join(baseFolder, '01_ANONYMIZACE', 'OUT'),
    // 02_DEANONYMIZACE
    deanonFolder: path.join(baseFolder, '02_DEANONYMIZACE'),
    deanonIn: path.join(baseFolder, '02_DEANONYMIZACE', 'IN'),
    deanonOut: path.join(baseFolder, '02_DEANONYMIZACE', 'OUT'),
    // 03_KONVERZE_PDF
    pdfFolder: path.join(baseFolder, '03_KONVERZE_PDF'),
    pdfIn: path.join(baseFolder, '03_KONVERZE_PDF', 'IN'),
    pdfOut: path.join(baseFolder, '03_KONVERZE_PDF', 'OUT'),
    // Shared
    error: path.join(baseFolder, 'ERROR'),
    logs: path.join(baseFolder, 'LOGS')
  };
}

// Ensure folders exist
function ensureSkryiFolders() {
  const folders = getSkryiFolders();
  for (const folder of Object.values(folders)) {
    if (!fs.existsSync(folder)) {
      fs.mkdirSync(folder, { recursive: true });
    }
  }
  return folders;
}

// Watcher process references (for all 3 watchers)
let watcherProcesses = {
  anon: null,
  deanon: null,
  pdf: null
};

// Helper to check if a watcher is running
function isWatcherRunning(type) {
  const proc = watcherProcesses[type];
  return proc !== null && proc.exitCode === null;
}

// Get folder status
ipcMain.handle("get-folder-status", async () => {
  const folders = ensureSkryiFolders();

  // Check autostart registry (Windows only)
  let autostartEnabled = false;
  if (process.platform === 'win32') {
    try {
      const { execSync } = require('child_process');
      const result = execSync('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v SKRYIWatcher 2>nul', { encoding: 'utf8' });
      autostartEnabled = result.includes('SKRYIWatcher');
    } catch {
      autostartEnabled = false;
    }
  }

  return {
    baseFolder: folders.base,
    // 01_ANONYMIZACE
    anonInFolder: folders.anonIn,
    anonOutFolder: folders.anonOut,
    anonWatcherRunning: isWatcherRunning('anon'),
    // 02_DEANONYMIZACE
    deanonInFolder: folders.deanonIn,
    deanonOutFolder: folders.deanonOut,
    deanonWatcherRunning: isWatcherRunning('deanon'),
    // 03_KONVERZE_PDF
    pdfInFolder: folders.pdfIn,
    pdfOutFolder: folders.pdfOut,
    pdfWatcherRunning: isWatcherRunning('pdf'),
    // Shared
    errorFolder: folders.error,
    logsFolder: folders.logs,
    autostartEnabled
  };
});

// Open folders - unified handler
ipcMain.handle("open-folder", async (event, folderType) => {
  const folders = ensureSkryiFolders();
  const folderMap = {
    'anon-in': folders.anonIn,
    'anon-out': folders.anonOut,
    'deanon-in': folders.deanonIn,
    'deanon-out': folders.deanonOut,
    'pdf-in': folders.pdfIn,
    'pdf-out': folders.pdfOut,
    'error': folders.error
  };
  const folderPath = folderMap[folderType];
  if (folderPath) {
    shell.openPath(folderPath);
  }
});

ipcMain.handle("open-skryi-folder", async () => {
  const folders = ensureSkryiFolders();
  shell.openPath(folders.base);
});

// Watcher scripts mapping
const WATCHER_SCRIPTS = {
  anon: 'skryi_watcher.py',
  deanon: 'deanon_watcher.py',
  pdf: 'pdf2docx_watcher.py'
};

// Start watcher - unified handler
ipcMain.handle("start-watcher", async (event, watcherType) => {
  // Default to 'anon' for backward compatibility
  const type = watcherType || 'anon';

  if (isWatcherRunning(type)) {
    return { success: true, message: `${type} watcher is already running` };
  }

  const scriptName = WATCHER_SCRIPTS[type];
  if (!scriptName) {
    return { success: false, error: `Unknown watcher type: ${type}` };
  }

  const watcherScript = resolveScript(scriptName);

  if (!fs.existsSync(watcherScript.path)) {
    return { success: false, error: `Watcher script not found: ${scriptName}` };
  }

  try {
    let proc;
    if (watcherScript.isExe) {
      proc = spawn(watcherScript.path, [], {
        detached: true,
        stdio: 'ignore',
        windowsHide: true
      });
    } else {
      const args = PY.isPyLauncher
        ? ["-3", watcherScript.path]
        : [watcherScript.path];

      proc = spawn(PY.cmd, args, {
        detached: true,
        stdio: 'ignore',
        windowsHide: true
      });
    }

    proc.unref();
    watcherProcesses[type] = proc;
    console.log(`[WATCHER-${type.toUpperCase()}] Started with PID:`, proc.pid);

    return { success: true, pid: proc.pid };
  } catch (error) {
    console.error(`[WATCHER-${type.toUpperCase()}] Start error:`, error);
    return { success: false, error: error.message };
  }
});

// Stop watcher - unified handler
ipcMain.handle("stop-watcher", async (event, watcherType) => {
  // Default to 'anon' for backward compatibility
  const type = watcherType || 'anon';
  const proc = watcherProcesses[type];

  if (proc) {
    try {
      // On Windows, use taskkill to ensure the process is terminated
      if (process.platform === 'win32') {
        const { execSync } = require('child_process');
        execSync(`taskkill /PID ${proc.pid} /F 2>nul`, { encoding: 'utf8' });
      } else {
        proc.kill('SIGTERM');
      }
      watcherProcesses[type] = null;
      return { success: true };
    } catch (error) {
      console.error(`[WATCHER-${type.toUpperCase()}] Stop error:`, error);
      watcherProcesses[type] = null;
      return { success: true }; // Consider it stopped even if error
    }
  }
  return { success: true, message: `${type} watcher was not running` };
});

// Enable autostart (Windows only)
ipcMain.handle("enable-autostart", async () => {
  if (process.platform !== 'win32') {
    return { success: false, error: "Autostart only supported on Windows" };
  }

  try {
    const watcherScript = resolveScript("skryi_watcher.py");
    let command;

    if (watcherScript.isExe) {
      command = `"${watcherScript.path}"`;
    } else {
      command = `"${PY.cmd}" "${watcherScript.path}"`;
    }

    const { execSync } = require('child_process');
    execSync(`reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v SKRYIWatcher /t REG_SZ /d "${command}" /f`, { encoding: 'utf8' });

    return { success: true };
  } catch (error) {
    console.error("[AUTOSTART] Enable error:", error);
    return { success: false, error: error.message };
  }
});

// Disable autostart (Windows only)
ipcMain.handle("disable-autostart", async () => {
  if (process.platform !== 'win32') {
    return { success: false, error: "Autostart only supported on Windows" };
  }

  try {
    const { execSync } = require('child_process');
    execSync('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v SKRYIWatcher /f 2>nul', { encoding: 'utf8' });
    return { success: true };
  } catch (error) {
    // Key might not exist, that's OK
    return { success: true };
  }
});
