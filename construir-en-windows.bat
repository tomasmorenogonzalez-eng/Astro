@echo off
rem Fabrica ASTRO.exe en este PC. Necesita Python 3 de python.org (marca "Add python.exe to PATH").
cd /d "%~dp0"
py -3 -m venv .entorno || python -m venv .entorno || goto fallo
call .entorno\Scripts\activate.bat || goto fallo
python -m pip install --upgrade pip pyinstaller pillow certifi pywebview sgp4 || goto fallo
pyinstaller ASTRO.spec --noconfirm || goto fallo
echo.
echo LISTO: la aplicacion esta en la carpeta dist (ASTRO.exe).
explorer dist
pause
exit /b 0

:fallo
echo.
echo NO SE HA PODIDO FABRICAR: mira los mensajes de arriba. Comprueba que Python 3 esta instalado desde python.org
echo y que marcaste "Add python.exe to PATH" al instalarlo.
pause
exit /b 1
