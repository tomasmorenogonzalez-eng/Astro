# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para fabricar la aplicación ASTRO en Mac, Windows y Linux:
#     pyinstaller ASTRO.spec --noconfirm
import os, sys

# version.txt y repo.txt los crea la fábrica de GitHub al publicar (permiten la actualización automática)
import re
VERSION = open("version.txt").read().strip() if os.path.exists("version.txt") else "1.0"
VERSION_MAC = ".".join(re.findall(r"\d+", VERSION)[:3]) or "1.0"     # el Mac solo admite números
extras = [(f, ".") for f in ("version.txt", "repo.txt", "contacto.txt") if os.path.exists(f)]

a = Analysis(
    ["lanzador.py"],
    datas=[("programa-lights.py", "."), ("programa-calibracion.py", "."), ("icono.png", "."), ("imagenes", "imagenes")] + extras,
    hiddenimports=["tkinter", "tkinter.filedialog", "tkinter.messagebox", "certifi"],
    excludes=["numpy", "matplotlib", "PIL", "pandas", "scipy"],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ASTRO", console=False, icon="icono.png")
    coll = COLLECT(exe, a.binaries, a.datas, name="ASTRO")
    app = BUNDLE(
        coll, name="ASTRO.app", icon="icono.png", bundle_identifier="es.astrocitas.astro",
        info_plist={
            "CFBundleName": "ASTRO", "CFBundleDisplayName": "ASTRO",
            "CFBundleShortVersionString": VERSION_MAC, "CFBundleVersion": VERSION_MAC,
            "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "Tomás Moreno González · Astrocitas · Asociación Astronómica Azarquiel · Asociación Astronómica de Miguelturra",
        },
    )
else:
    # Windows y Linux: un único archivo ejecutable
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="ASTRO", console=False, icon="icono.png",
              upx=False, runtime_tmpdir=None)
