"use strict";

const path = require("path");
const { app, BrowserWindow, ipcMain, shell } = require("electron");
const { scanInstalledGames } = require("./scanner.cjs");
const trainerRuntime = require("./trainer-runtime.cjs");

function desktopIndexPath() {
  return path.join(__dirname, "..", "desktop", "index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 1024,
    minHeight: 680,
    backgroundColor: "#0e1113",
    title: "SoloForge",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  win.removeMenu();
  win.loadFile(desktopIndexPath());
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://") || url.startsWith("http://")) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });
}

ipcMain.handle("soloforge:scan-installed-games", async () => {
  try {
    return {
      ok: true,
      payload: await scanInstalledGames(),
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
});

async function safeNativeCall(action) {
  try {
    return {
      ok: true,
      payload: await action(),
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

ipcMain.handle("soloforge:trainer-runtime-status", async () =>
  safeNativeCall(() => trainerRuntime.trainerRuntimeStatus()),
);

ipcMain.handle("soloforge:list-trainer-processes", async () =>
  safeNativeCall(() => trainerRuntime.listTrainerProcesses()),
);

ipcMain.handle("soloforge:first-trainer-scan", async (_event, request) =>
  safeNativeCall(() => trainerRuntime.firstTrainerScan(request)),
);

ipcMain.handle("soloforge:narrow-trainer-scan", async (_event, request) =>
  safeNativeCall(() => trainerRuntime.narrowTrainerScan(request)),
);

ipcMain.handle("soloforge:write-trainer-value", async (_event, request) =>
  safeNativeCall(() => trainerRuntime.writeTrainerValue(request)),
);

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
