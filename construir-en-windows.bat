@echo off
rem Fabrica ASTRO.exe en este PC. Necesita Python 3 de python.org (marca "Add python.exe to PATH").
cd /d "%~dp0"
py -3 -m venv .entorno || python -m venv .entorno
call .entorno\Scripts\activate.bat
pip install --upgrade pip pyinstaller pillow certifi pywebview
pyinstaller ASTRO.spec --noconfirm
echo.
echo LISTO: la aplicacion esta en la carpeta dist (ASTRO.exe).
explorer dist
pause
