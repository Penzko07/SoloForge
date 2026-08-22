# macOS App

SoloForge can be built as a local macOS `.app` without Electron or npm.

## Build

```bash
bash tools/build_macos_app.sh
```

The build creates:

```text
build/macos/SoloForge.app
```

To create a shareable zip:

```bash
ditto -c -k --sequesterRsrc --keepParent build/macos/SoloForge.app build/macos/SoloForge-macos.zip
```

## What Is Bundled

The app bundle contains:

- the static desktop UI from `apps/desktop`
- the local launcher scanner tools from `tools`
- the normalized registry from `registry`
- a small Objective-C/AppKit/WebKit launcher from `apps/macos`

## Native Scanner Bridge

The desktop UI sends this message inside the macOS app:

```js
window.webkit.messageHandlers.soloforge.postMessage({ type: "scanInstalledGames" });
```

The native wrapper runs:

```bash
python3 tools/scan_installed_games.py --all-drives --pretty
```

The JSON result is returned to the UI through a `soloforge-native-scan` browser event.

## Current Limits

This app is ad-hoc signed for local testing, not notarized by Apple yet. On first launch, macOS may require opening it from Finder with the context menu or approving it in Privacy & Security.

The bundled scanner only reads local launcher metadata. It does not attach to game processes.
