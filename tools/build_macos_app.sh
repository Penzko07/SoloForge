#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT/build/macos/SoloForge.app"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

python3 "$ROOT/tools/update_app_data.py"

rm -rf "$APP_DIR"
mkdir -p "$MACOS" "$RESOURCES"

cp "$ROOT/apps/macos/Info.plist" "$CONTENTS/Info.plist"
cp -R "$ROOT/apps/desktop" "$RESOURCES/desktop"
cp -R "$ROOT/tools" "$RESOURCES/tools"
cp -R "$ROOT/registry" "$RESOURCES/registry"

find "$RESOURCES" -name "__pycache__" -type d -prune -exec rm -rf {} +
find "$RESOURCES/tools" -type f \( -name "*.py" -o -name "*.sh" \) -exec chmod +x {} +

clang \
  "$ROOT/apps/macos/main.m" \
  -o "$MACOS/SoloForge" \
  -fobjc-arc \
  -framework Cocoa \
  -framework WebKit

if command -v xattr >/dev/null 2>&1; then
  xattr -cr "$APP_DIR" || true
fi

if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP_DIR" >/dev/null || echo "Warning: ad-hoc signing failed; app bundle was still built." >&2
fi

echo "$APP_DIR"
