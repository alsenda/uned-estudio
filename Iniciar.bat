@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Estudio UNED
rem Busca un Python que funcione de verdad (el "python" falso de la Microsoft Store no cuenta).
set "PY="
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY (
  python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo No encuentro Python instalado.
  echo Instalalo desde https://www.python.org/downloads/release/python-3128/
  echo ^(baja hasta "Files" y elige "Windows installer 64-bit"^) y marca la casilla
  echo "Add python.exe to PATH" durante la instalacion. Despues vuelve a abrir este fichero.
  pause
  exit /b 1
)
%PY% iniciar.py %*
if errorlevel 1 pause
