@echo off
echo ====================================================
echo D-CASCADE QGIS Plugin Development Installation
echo ====================================================
echo.

echo Running consolidated development installer...
echo This will link the plugin, install dependencies, and fetch model files.
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install_plugin_dev.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Development installation failed!
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo ====================================================
echo Development installation complete!
echo ====================================================
echo Please restart QGIS and enable the D-CASCADE plugin
echo via Plugins -^> Manage and Install Plugins
echo.
pause
