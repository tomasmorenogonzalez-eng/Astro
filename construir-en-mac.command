#!/bin/bash
# Fabrica ASTRO.app en este Mac. Necesita Python 3 de python.org (https://www.python.org/downloads/).
cd "$(dirname "$0")"
python3 -m venv .entorno && source .entorno/bin/activate \
  && pip install --upgrade pip pyinstaller pillow certifi \
  && pyinstaller ASTRO.spec --noconfirm \
  && codesign --force --deep -s - dist/ASTRO.app \
  && echo "" && echo "LISTO: la aplicación está en la carpeta dist (ASTRO.app)." && open dist
