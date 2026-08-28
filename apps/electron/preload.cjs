"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("soloforgeNative", {
  appKind: "electron",
  platform: process.platform,
  scanInstalledGames: () => ipcRenderer.invoke("soloforge:scan-installed-games"),
  trainerRuntimeStatus: () => ipcRenderer.invoke("soloforge:trainer-runtime-status"),
  listTrainerProcesses: () => ipcRenderer.invoke("soloforge:list-trainer-processes"),
  firstTrainerScan: (request) => ipcRenderer.invoke("soloforge:first-trainer-scan", request),
  narrowTrainerScan: (request) => ipcRenderer.invoke("soloforge:narrow-trainer-scan", request),
  writeTrainerValue: (request) => ipcRenderer.invoke("soloforge:write-trainer-value", request),
});
