"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const REGISTRY_GAMES = path.join(ROOT, "registry", "games");
const WINDOWS_HELPER = path.join(__dirname, "windows-memory-helper.ps1");
const VALUE_TYPES = new Set(["int32", "float", "double"]);

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function loadRegistryGames() {
  if (!fs.existsSync(REGISTRY_GAMES)) return [];
  return fs
    .readdirSync(REGISTRY_GAMES)
    .filter((name) => name.endsWith(".json"))
    .map((name) => readJson(path.join(REGISTRY_GAMES, name)));
}

function trainerRuntimeStatus() {
  const available = process.platform === "win32" && fs.existsSync(WINDOWS_HELPER);
  return {
    platform: process.platform,
    available,
    engine: available ? "windows-memory-helper" : "simulation-only",
    helper: available ? WINDOWS_HELPER : null,
    mode: available ? "native-memory" : "preview",
  };
}

function assertWindowsRuntime() {
  const status = trainerRuntimeStatus();
  if (!status.available) {
    throw new Error("Native memory scanning is available only in the Windows desktop app.");
  }
}

function assertTrainerTarget(request) {
  if (request?.strictlyMultiplayer) {
    throw new Error("Strictly multiplayer games are outside SoloForge.");
  }
  if (request?.userConfirmedOffline !== true) {
    throw new Error("Confirm offline singleplayer mode before scanning or writing memory.");
  }

  const games = loadRegistryGames();
  if (request?.gameId) {
    const game = games.find((item) => item.id === request.gameId);
    if (!game) throw new Error(`Unknown registry game: ${request.gameId}`);
    const safety = game.safety || {};
    if (!safety.singleplayerOnly || !safety.offlineOnly || !safety.multiplayerBlocked) {
      throw new Error(`${game.name} is not marked as an offline singleplayer target.`);
    }
    return {
      gameId: game.id,
      gameName: game.name,
      executableHints: game.game?.executables || [],
    };
  }

  const customGameName = String(request?.customGameName || "").trim();
  if (customGameName.length < 2) {
    throw new Error("Choose a registry game or enter a custom offline singleplayer game name.");
  }
  return { gameId: null, gameName: customGameName, executableHints: [] };
}

function normalizePid(pid) {
  const value = Number(pid);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error("A running game process is required.");
  }
  return value;
}

function normalizeValueType(valueType) {
  const normalized = String(valueType || "").toLowerCase();
  if (!VALUE_TYPES.has(normalized)) throw new Error(`Unsupported value type: ${valueType}`);
  return normalized;
}

function normalizeValue(value) {
  if (value === null || value === undefined || value === "") throw new Error("A scan value is required.");
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) throw new Error("Scan value must be numeric.");
  return String(value);
}

function normalizeAddresses(candidates) {
  if (!Array.isArray(candidates) || candidates.length === 0) {
    throw new Error("No candidate addresses were provided.");
  }
  return candidates
    .map((candidate) => String(candidate.address || candidate))
    .filter((address) => /^0x[0-9a-f]+$/i.test(address))
    .slice(0, 512);
}

function powershellPath() {
  if (process.env.SystemRoot) {
    return path.join(process.env.SystemRoot, "System32", "WindowsPowerShell", "v1.0", "powershell.exe");
  }
  return "powershell.exe";
}

function runWindowsHelper(request, timeoutMs = 120000) {
  assertWindowsRuntime();
  return new Promise((resolve, reject) => {
    childProcess.execFile(
      powershellPath(),
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", WINDOWS_HELPER, JSON.stringify(request)],
      {
        encoding: "utf8",
        maxBuffer: 12 * 1024 * 1024,
        timeout: timeoutMs,
        windowsHide: true,
      },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(stderr.trim() || error.message));
          return;
        }
        try {
          const payload = JSON.parse(stdout.trim() || "{}");
          if (payload.ok === false) reject(new Error(payload.error || "Native helper failed."));
          else resolve(payload);
        } catch (parseError) {
          reject(new Error(`Native helper returned invalid JSON: ${parseError.message}`));
        }
      },
    );
  });
}

async function listTrainerProcesses() {
  if (!trainerRuntimeStatus().available) {
    return { available: false, processes: [] };
  }
  return runWindowsHelper({ action: "listProcesses" }, 30000);
}

async function firstTrainerScan(request) {
  const target = assertTrainerTarget(request);
  const pid = normalizePid(request.pid);
  const valueType = normalizeValueType(request.valueType);
  const value = normalizeValue(request.value);
  return runWindowsHelper({
    action: "firstScan",
    pid,
    valueType,
    value,
    candidateLimit: 256,
    maxBytes: 536870912,
    maxRegionBytes: 33554432,
    target,
  });
}

async function narrowTrainerScan(request) {
  const target = assertTrainerTarget(request);
  const pid = normalizePid(request.pid);
  const valueType = normalizeValueType(request.valueType);
  const value = normalizeValue(request.value);
  const addresses = normalizeAddresses(request.candidates);
  return runWindowsHelper({
    action: "narrowScan",
    pid,
    valueType,
    value,
    addresses,
    target,
  });
}

async function writeTrainerValue(request) {
  const target = assertTrainerTarget(request);
  const pid = normalizePid(request.pid);
  const valueType = normalizeValueType(request.valueType);
  const value = normalizeValue(request.value);
  const [address] = normalizeAddresses([request.address]);
  return runWindowsHelper({
    action: "writeValue",
    pid,
    valueType,
    value,
    address,
    target,
  });
}

if (require.main === module) {
  const pretty = process.argv.includes("--pretty");
  process.stdout.write(JSON.stringify(trainerRuntimeStatus(), null, pretty ? 2 : 0));
  process.stdout.write("\n");
}

module.exports = {
  firstTrainerScan,
  listTrainerProcesses,
  narrowTrainerScan,
  trainerRuntimeStatus,
  writeTrainerValue,
};
