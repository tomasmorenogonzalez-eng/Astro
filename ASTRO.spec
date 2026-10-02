# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para fabricar la aplicación ASTRO en Mac, Windows y Linux:
#     pyinstaller ASTRO.spec --noconfirm
import os, sys

# version.txt y repo.txt los crea la fábrica de GitHub al publicar (permiten la actualización automática)
import re
VERSION = open("version.txt").read().strip() if os.path.exists("version.txt") else "0.0"
VERSION_MAC = ".".join(re.findall(r"\d+", VERSION)[:3]) or "1.0"     # el Mac solo admite números
extras = [(f, ".") for f in ("version.txt", "repo.txt", "contacto.txt", "donar.txt", "cursos.txt") if os.path.exists(f)]

# Los programas van como datos (se ejecutan dentro de la aplicación), así que el empaquetador no ve lo que importan:
# se leen sus «import» y se añaden todos, para que ninguno falte en la aplicación.
import ast
EXCLUIDOS = ["numpy", "matplotlib", "PIL", "pandas", "scipy"]
def _importados(archivo):
    mods = set()
    for n in ast.walk(ast.parse(open(archivo, encoding="utf-8").read())):
        if isinstance(n, ast.Import):
            mods.update(x.name for x in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            mods.add(n.module)
    return mods
PROGRAMAS = ["programa-lights.py", "programa-calibracion.py", "programa-ciencia.py"]
DE_LOS_PROGRAMAS = sorted(m for p in PROGRAMAS for m in _importados(p) if m.split(".")[0] not in EXCLUIDOS)

# La ventana propia (pywebview): en el Mac usa WebKit (pyobjc) y en Windows WebView2 (pythonnet). Los demás
# motores que pywebview sabe usar (Qt, GTK, CEF) no hacen falta y no se meten aunque estén instalados.
VENTANA = []
if sys.platform == "darwin":
    VENTANA = ["webview", "webview.platforms.cocoa"]
elif sys.platform.startswith("win"):
    VENTANA = ["webview", "webview.platforms.winforms", "webview.platforms.edgechromium", "clr"]
SIN_VENTANA = ["webview.platforms.qt", "webview.platforms.gtk", "webview.platforms.cef", "webview.platforms.android",
               "qtpy", "PyQt5", "PyQt6", "PySide2", "PySide6", "gi", "cefpython3"]
try:
    import webview  # noqa: F401  (si no está instalado, ASTRO se abre en el navegador, como antes)
except Exception:
    VENTANA = []

a = Analysis(
    ["lanzador.py"],
    datas=[(p, ".") for p in PROGRAMAS] + [("icono.png", "."), ("imagenes", "imagenes"), ("idiomas", "idiomas"), ("cielo", "cielo"), ("demo", "demo"), ("novedades.json", ".")] + extras,
    hiddenimports=["tkinter", "tkinter.filedialog", "tkinter.messagebox", "certifi"] + DE_LOS_PROGRAMAS + VENTANA,
    excludes=EXCLUIDOS + SIN_VENTANA,
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
            "NSHumanReadableCopyright": "Raúl Hussein Galindo · Tomás Moreno González",
        },
    )
else:
    # Windows y Linux: un único archivo ejecutable
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="ASTRO", console=False, icon="icono.png",
              upx=False, runtime_tmpdir=None)
