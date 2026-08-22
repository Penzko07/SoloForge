"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const REGISTRY_GAMES = path.join(ROOT, "registry", "games");
const LAUNCHER_PLATFORMS = {
  steam: "steam",
  gog: "gog",
  ubisoft: "ubisoft-connect",
  ea: "ea-app",
};
const JSON_NAME_KEYS = ["name", "title", "gameName", "displayName", "productTitle"];
const JSON_ID_KEYS = ["gameId", "game_id", "productId", "product_id", "rootGameId", "appId", "app_id", "id"];
const JSON_PATH_KEYS = ["installPath", "install_path", "installationPath", "installation_path", "path", "installDir"];

function exists(target) {
  if (typeof target !== "string" || !target) return false;
  try {
    return fs.existsSync(target);
  } catch {
    return false;
  }
}

function readText(target) {
  return fs.readFileSync(target, "utf8");
}

function unique(values) {
  const seen = new Set();
  return values.filter((value) => {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function envPath(name, ...parts) {
  return process.env[name] ? path.join(process.env[name], ...parts) : null;
}

function normalizeTitle(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function loadRegistryGames() {
  if (!exists(REGISTRY_GAMES)) return [];
  return fs
    .readdirSync(REGISTRY_GAMES)
    .filter((name) => name.endsWith(".json"))
    .map((name) => JSON.parse(readText(path.join(REGISTRY_GAMES, name))));
}

function matchRegistryGame(launcher, storeId, title, registryGames) {
  const platform = LAUNCHER_PLATFORMS[launcher];
  const normalized = normalizeTitle(title);

  if (storeId) {
    const byId = registryGames.find((game) => game.game?.storeIds?.[platform] === String(storeId));
    if (byId) return byId;
  }

  return registryGames.find((game) => normalizeTitle(game.game?.title || game.name) === normalized) || null;
}

function buildGameRecord(launcher, name, storeId, installDir, manifestPath, registryGames) {
  const match = matchRegistryGame(launcher, storeId, name, registryGames);
  return {
    name,
    launcher,
    platform: LAUNCHER_PLATFORMS[launcher],
    storeId: storeId || null,
    installDir: installDir || null,
    manifestPath: manifestPath || null,
    match: Boolean(match),
    registryId: match?.id || null,
    safetyStatus: match?.safety?.reviewStatus || "requiresManualReview",
    singleplayerEligible: Boolean(
      match?.safety?.singleplayerOnly && match?.safety?.offlineOnly && match?.safety?.multiplayerBlocked,
    ),
    achievementCompatibility: "neutral-by-policy",
    availableFeatures: match?.features?.map((feature) => feature.name) || [],
  };
}

function tokenizeVdf(text) {
  const tokens = [];
  const pattern = /"((?:\\.|[^"\\])*)"|([{}])/g;
  let match;
  while ((match = pattern.exec(text))) {
    if (match[1] !== undefined) {
      tokens.push(match[1].replace(/\\"/g, '"').replace(/\\\\/g, "\\"));
    } else {
      tokens.push(match[2]);
    }
  }
  return tokens;
}

function parseVdf(text) {
  const tokens = tokenizeVdf(text);
  let index = 0;

  function parseObject() {
    const object = {};
    while (index < tokens.length && tokens[index] !== "}") {
      const key = tokens[index++];
      if (tokens[index] === "{") {
        index += 1;
        object[key] = parseObject();
        if (tokens[index] === "}") index += 1;
      } else {
        object[key] = tokens[index++] || "";
      }
    }
    return object;
  }

  return parseObject();
}

function windowsSteamPathFromRegistry() {
  if (process.platform !== "win32") return null;
  try {
    const output = childProcess.execFileSync(
      "reg",
      ["query", "HKCU\\Software\\Valve\\Steam", "/v", "SteamPath"],
      { encoding: "utf8", windowsHide: true },
    );
    const line = output.split(/\r?\n/).find((item) => item.includes("SteamPath"));
    const value = line?.match(/REG_\w+\s+(.+)$/)?.[1]?.trim();
    return value ? value.replace(/\//g, "\\") : null;
  } catch {
    return null;
  }
}

function mountedDriveRoots() {
  if (process.platform === "win32") {
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      .split("")
      .map((letter) => `${letter}:\\`)
      .filter(exists);
  }

  if (process.platform === "darwin") {
    const volumes = "/Volumes";
    return exists(volumes) ? fs.readdirSync(volumes).map((name) => path.join(volumes, name)).filter(exists) : [];
  }

  return ["/mnt", "/media"]
    .filter(exists)
    .flatMap((root) => fs.readdirSync(root).map((name) => path.join(root, name)).filter(exists));
}

function launcherRootsFromDrives(launcher) {
  const candidates = [];
  for (const drive of mountedDriveRoots()) {
    if (launcher === "steam") {
      candidates.push(
        path.join(drive, "Steam"),
        path.join(drive, "SteamLibrary"),
        path.join(drive, "Games", "Steam"),
        path.join(drive, "Games", "SteamLibrary"),
        path.join(drive, "Program Files", "Steam"),
        path.join(drive, "Program Files (x86)", "Steam"),
      );
    } else if (launcher === "gog") {
      candidates.push(
        path.join(drive, "GOG Games"),
        path.join(drive, "Games", "GOG Games"),
        path.join(drive, "GOG Galaxy", "Games"),
        path.join(drive, "Program Files", "GOG Galaxy", "Games"),
        path.join(drive, "Program Files (x86)", "GOG Galaxy", "Games"),
      );
    } else if (launcher === "ubisoft") {
      candidates.push(
        path.join(drive, "Ubisoft Games"),
        path.join(drive, "Games", "Ubisoft Games"),
        path.join(drive, "Program Files", "Ubisoft", "Ubisoft Game Launcher"),
        path.join(drive, "Program Files (x86)", "Ubisoft", "Ubisoft Game Launcher"),
      );
    } else if (launcher === "ea") {
      candidates.push(
        path.join(drive, "EA Games"),
        path.join(drive, "Games", "EA Games"),
        path.join(drive, "Program Files", "EA Games"),
        path.join(drive, "Program Files", "Electronic Arts"),
        path.join(drive, "Program Files (x86)", "Electronic Arts"),
      );
    }
  }
  return candidates.filter(exists);
}

function defaultRoots(launcher) {
  const home = os.homedir();
  const roots = [];

  if (launcher === "steam") {
    roots.push(
      windowsSteamPathFromRegistry(),
      envPath("ProgramFiles(x86)", "Steam"),
      envPath("ProgramFiles", "Steam"),
      path.join(home, "Library", "Application Support", "Steam"),
      path.join(home, ".steam", "steam"),
      path.join(home, ".local", "share", "Steam"),
    );
  } else if (launcher === "gog") {
    roots.push(
      envPath("ProgramData", "GOG.com", "Galaxy", "storage"),
      envPath("ProgramFiles", "GOG Galaxy", "Games"),
      envPath("ProgramFiles(x86)", "GOG Galaxy", "Games"),
      envPath("USERPROFILE", "GOG Games"),
      path.join(home, "Library", "Application Support", "GOG.com", "Galaxy", "storage"),
      path.join(home, "GOG Games"),
    );
  } else if (launcher === "ubisoft") {
    roots.push(
      envPath("ProgramFiles(x86)", "Ubisoft", "Ubisoft Game Launcher"),
      envPath("ProgramFiles", "Ubisoft", "Ubisoft Game Launcher"),
      envPath("ProgramData", "Ubisoft"),
      path.join(home, "Library", "Application Support", "Ubisoft"),
    );
  } else if (launcher === "ea") {
    roots.push(
      envPath("ProgramData", "EA Desktop"),
      envPath("ProgramFiles", "EA Games"),
      envPath("ProgramFiles", "Electronic Arts"),
      envPath("ProgramFiles(x86)", "Electronic Arts"),
      path.join(home, "Library", "Application Support", "Electronic Arts"),
    );
  }

  return unique([...roots, ...launcherRootsFromDrives(launcher)].filter(exists));
}

function steamLibrariesFromRoot(root) {
  const libraries = [root];
  const libraryFile = path.join(root, "steamapps", "libraryfolders.vdf");
  if (!exists(libraryFile)) return libraries;

  try {
    const parsed = parseVdf(readText(libraryFile));
    const folders = parsed.libraryfolders || parsed.LibraryFolders || parsed;
    for (const value of Object.values(folders)) {
      if (typeof value === "string") libraries.push(value);
      if (value && typeof value === "object" && typeof value.path === "string") libraries.push(value.path);
    }
  } catch {
    return libraries;
  }

  return unique(libraries.filter(exists));
}

function scanSteam(registryGames) {
  const errors = [];
  const libraries = unique(defaultRoots("steam").flatMap(steamLibrariesFromRoot));
  const games = [];

  for (const library of libraries) {
    const steamapps = path.join(library, "steamapps");
    if (!exists(steamapps)) continue;
    for (const file of fs.readdirSync(steamapps).filter((name) => /^appmanifest_\d+\.acf$/.test(name))) {
      const manifest = path.join(steamapps, file);
      try {
        const parsed = parseVdf(readText(manifest));
        const state = parsed.AppState || parsed.appstate || parsed;
        const name = state.name || `Steam game ${state.appid || file}`;
        const installDir = state.installdir ? path.join(steamapps, "common", state.installdir) : null;
        games.push(buildGameRecord("steam", name, state.appid, installDir, manifest, registryGames));
      } catch (error) {
        errors.push({ launcher: "steam", path: manifest, error: error.message });
      }
    }
  }

  return {
    libraries: libraries.map((library) => ({ launcher: "steam", path: library })),
    games,
    errors,
  };
}

function walkFiles(root, options = {}) {
  const maxDepth = options.maxDepth ?? 5;
  const maxFiles = options.maxFiles ?? 2000;
  const files = [];

  function visit(current, depth) {
    if (files.length >= maxFiles || depth > maxDepth) return;
    let entries = [];
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      if (files.length >= maxFiles) return;
      const target = path.join(current, entry.name);
      if (entry.isDirectory()) {
        visit(target, depth + 1);
      } else if (entry.isFile()) {
        files.push(target);
      }
    }
  }

  if (exists(root)) visit(root, 0);
  return files;
}

function firstString(record, keys) {
  for (const key of keys) {
    const exact = record[key];
    if (typeof exact === "string" && exact.trim()) return exact.trim();
    if (typeof exact === "number") return String(exact);
    const found = Object.entries(record).find(([name]) => name.toLowerCase() === key.toLowerCase())?.[1];
    if (typeof found === "string" && found.trim()) return found.trim();
    if (typeof found === "number") return String(found);
  }
  return null;
}

function flattenJson(value) {
  if (Array.isArray(value)) return value.flatMap(flattenJson);
  if (!value || typeof value !== "object") return [];
  return [value, ...Object.values(value).flatMap(flattenJson)];
}

function scanGogInfoFile(file, registryGames) {
  const payload = JSON.parse(readText(file));
  const name = firstString(payload, JSON_NAME_KEYS);
  const storeId = firstString(payload, JSON_ID_KEYS) || path.basename(file).match(/goggame-(\d+)/)?.[1] || null;
  const installDir = firstString(payload, JSON_PATH_KEYS) || path.dirname(file);
  if (!name && !storeId) return null;
  return buildGameRecord("gog", name || `GOG game ${storeId}`, storeId, installDir, file, registryGames);
}

function scanJsonManifest(file, launcher, registryGames) {
  let payload;
  try {
    payload = JSON.parse(readText(file));
  } catch {
    return null;
  }

  for (const record of flattenJson(payload)) {
    const name = firstString(record, JSON_NAME_KEYS);
    const storeId = firstString(record, JSON_ID_KEYS);
    const installDir = firstString(record, JSON_PATH_KEYS);
    if (name && (storeId || installDir)) {
      return buildGameRecord(launcher, name, storeId, installDir || path.dirname(file), file, registryGames);
    }
  }
  return null;
}

function textBetween(text, names) {
  for (const name of names) {
    const pattern = new RegExp(`<${name}[^>]*>([^<]+)</${name}>`, "i");
    const match = text.match(pattern);
    if (match?.[1]?.trim()) return match[1].trim();
  }
  return null;
}

function scanEaXml(file, registryGames) {
  const xml = readText(file);
  const name = textBetween(xml, ["title", "name", "displayName"]);
  const storeId = textBetween(xml, ["contentID", "contentId", "productId", "gameId", "id"]);
  const installDir = textBetween(xml, ["installPath", "installationPath", "path"]) || path.dirname(file);
  if (!name && !storeId) return null;
  return buildGameRecord("ea", name || `EA game ${storeId}`, storeId, installDir, file, registryGames);
}

function scanManifestLauncher(launcher, registryGames) {
  const roots = defaultRoots(launcher);
  const games = [];
  const errors = [];

  for (const root of roots) {
    const files = walkFiles(root, { maxDepth: 5, maxFiles: 2500 });
    for (const file of files) {
      try {
        let record = null;
        const base = path.basename(file).toLowerCase();
        const ext = path.extname(file).toLowerCase();

        if (launcher === "gog" && base.startsWith("goggame-") && base.endsWith(".info")) {
          record = scanGogInfoFile(file, registryGames);
        } else if ([".json", ".manifest"].includes(ext)) {
          record = scanJsonManifest(file, launcher, registryGames);
        } else if (launcher === "ea" && [".xml", ".mfst"].includes(ext)) {
          record = scanEaXml(file, registryGames);
        }

        if (record) games.push(record);
      } catch (error) {
        errors.push({ launcher, path: file, error: error.message });
      }
    }
  }

  return {
    libraries: roots.map((root) => ({ launcher, path: root })),
    games,
    errors,
  };
}

function dedupeGames(games) {
  const seen = new Set();
  return games.filter((game) => {
    const key = [game.launcher, game.storeId || normalizeTitle(game.name), game.installDir || ""].join(":");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

async function scanInstalledGames() {
  const registryGames = loadRegistryGames();
  const steam = scanSteam(registryGames);
  const gog = scanManifestLauncher("gog", registryGames);
  const ubisoft = scanManifestLauncher("ubisoft", registryGames);
  const ea = scanManifestLauncher("ea", registryGames);
  const scanners = ["steam", "gog", "ubisoft", "ea"];

  return {
    generatedBy: "apps/electron/scanner.cjs",
    generatedAt: new Date().toISOString(),
    platform: process.platform,
    scanners,
    libraries: [...steam.libraries, ...gog.libraries, ...ubisoft.libraries, ...ea.libraries],
    games: dedupeGames([...steam.games, ...gog.games, ...ubisoft.games, ...ea.games]).sort((a, b) =>
      `${a.launcher}:${a.name}`.localeCompare(`${b.launcher}:${b.name}`),
    ),
    errors: [...steam.errors, ...gog.errors, ...ubisoft.errors, ...ea.errors],
  };
}

if (require.main === module) {
  scanInstalledGames()
    .then((result) => {
      const pretty = process.argv.includes("--pretty");
      process.stdout.write(JSON.stringify(result, null, pretty ? 2 : 0));
      process.stdout.write("\n");
    })
    .catch((error) => {
      console.error(error);
      process.exitCode = 1;
    });
}

module.exports = {
  parseVdf,
  scanInstalledGames,
};
