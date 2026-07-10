#!/usr/bin/env bash
# MathOCR macOS DMG packager by Bouronikos Christos <chrisbouronikos@gmail.com>.
# Support development: https://paypal.me/christosbouronikos

set -euo pipefail

APP_PATH="dist/MathOCR.app"
ARCH="$(uname -m)"
DMG_PATH="dist/MathOCR-macOS-${ARCH}.dmg"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Missing $APP_PATH; run python scripts/build_desktop.py first." >&2
  exit 1
fi

# Signing/notarization is deliberately a release-credential step; see README.
hdiutil create -volname "MathOCR" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
echo "macOS installer created: $DMG_PATH"

