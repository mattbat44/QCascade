@echo off
echo ====================================================
echo D-CASCADE QGIS Plugin Installation Script
echo ====================================================
echo.

echo [1/3] Installing plugin in development mode...
echo This will create a symbolic link in the QGIS plugins directory
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install_plugin_dev.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Plugin development installation failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [1/3] Complete
echo.

echo [2/3] Setting up QGIS Python environment...
echo This configures environment variables for QGIS Python
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0setup_qgis_environment.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: QGIS environment setup failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [2/3] Complete
echo.

echo [3/3] Installing dependencies to QGIS Python...
echo This installs required Python packages (numpy, pandas, geopandas, matplotlib)
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install_to_qgis_python.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Dependency installation failed!
    pause
    exit /b %ERRORLEVEL%
)
echo [3/3] Complete
echo.

echo ====================================================
echo Installation Complete!
echo ====================================================
echo Please restart QGIS and enable the D-CASCADE plugin
echo via Plugins -^> Manage and Install Plugins
echo.
pause