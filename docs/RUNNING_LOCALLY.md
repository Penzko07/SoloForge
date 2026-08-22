# Running Locally

SoloForge has a static browser UI, a Windows/Linux Electron app, and a native macOS wrapper.

## Electron App

Install dependencies:

```bash
npm install
```

Run the app:

```bash
npm start
```

Build Windows and Linux packages on the matching platform:

```bash
npm run dist:win
npm run dist:linux
```

## Open Directly

```text
apps/desktop/index.html
```

## Serve for Chrome

Chrome behaves more predictably when the MVP is served over local HTTP:

```bash
python3 tools/serve_desktop_app.py --open
```

Default URL:

```text
http://127.0.0.1:8765/
```

Use another port if needed:

```bash
python3 tools/serve_desktop_app.py --port 8777 --open
```
