#!/usr/bin/env bash
# MathOCR source launcher for macOS by Bouronikos Christos <chrisbouronikos@gmail.com>.
# Support development: https://paypal.me/christosbouronikos
#
# Double-click this file (or run it in Terminal) to start MathOCR from source.
# It makes sure Python 3 and Tesseract are installed, then hands over to
# scripts/launch.py. End users of the packaged app do NOT need this.

set -euo pipefail
cd "$(dirname "$0")"

PY_VERSION="3.11.9"

install_python() {
  echo "Python 3 was not found. Installing it now…"
  if command -v brew >/dev/null 2>&1; then
    brew install python@3.11
  else
    pkg="${TMPDIR:-/tmp}/python-${PY_VERSION}.pkg"
    echo "Downloading the official Python ${PY_VERSION} installer…"
    curl -fL -o "$pkg" "https://www.python.org/ftp/python/${PY_VERSION}/python-${PY_VERSION}-macos11.pkg"
    echo "Installing Python (you may be asked for your password)…"
    sudo installer -pkg "$pkg" -target /
  fi
}

if ! command -v python3 >/dev/null 2>&1; then
  install_python
fi

# Tesseract powers Greek/English page-text recognition. Math OCR works without
# it, so a failed install is only a warning, not a hard stop.
if ! command -v tesseract >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing Tesseract (Greek + English) for document text recognition…"
    brew install tesseract tesseract-lang || echo "Could not install Tesseract; page-text recognition will be unavailable."
  else
    echo "Note: install Tesseract (with the Greek 'ell' data) to read page text; math recognition works without it."
  fi
fi

exec python3 scripts/launch.py "$@"
