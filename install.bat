@echo off
echo ====================================================
echo Q-Cascade QGIS Plugin Basic Installation
echo ====================================================
echo.

echo This installs the plugin for the default QGIS profile
echo and installs Python dependencies into QGIS automatically.
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install_basic_user.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Installation failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo ====================================================
echo Installation Complete!
echo ====================================================
echo Please restart QGIS and enable the Q-Cascade plugin
echo via Plugins -^> Manage and Install Plugins
echo.
pause