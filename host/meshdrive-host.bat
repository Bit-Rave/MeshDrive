@echo off
REM Script batch pour Windows pour faciliter l'utilisation du CLI MeshDrive Host

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

python "%PROJECT_ROOT%\host\cli.py" %*

