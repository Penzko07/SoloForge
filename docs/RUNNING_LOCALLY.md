# Running Locally

SoloForge is currently a static web MVP, not a signed native installer.

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
