"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("soloforgeNative", {
  appKind: "electron",
  platform: process.platform,
  scanInstalledGames: () => ipcRenderer.invoke("soloforge:scan-installed-games"),
});
