# install_to_qgis_python.ps1
# Installs dependencies directly into QGIS's Python environment
# This ensures QGIS uses the correct numpy version (1.x)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Install D-CASCADE Dependencies to QGIS Python" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Find QGIS installation
$qgisPaths = @(
    "C:\Program Files\QGIS 3.34",
    "C:\Program Files\QGIS 3.38",
    "C:\Program Files\QGIS 3.40",
    "C:\OSGeo4W",
    "C:\OSGeo4W64"
)

$qgisPath = $null
foreach ($path in $qgisPaths) {
    if (Test-Path $path) {
        $qgisPath = $path
        break
    }
}

if (-not $qgisPath) {
    Write-Host "ERROR: Could not find QGIS installation" -ForegroundColor Red
    Write-Host "Checked paths:" -ForegroundColor Yellow
    foreach ($path in $qgisPaths) {
        Write-Host "  - $path" -ForegroundColor White
    }
    Write-Host ""
    $customPath = Read-Host "Enter QGIS installation path (or press Enter to exit)"
    if ($customPath -and (Test-Path $customPath)) {
        $qgisPath = $customPath
    } else {
        exit 1
    }
}

Write-Host "Found QGIS at: $qgisPath" -ForegroundColor Green
Write-Host ""

# Find python.exe in QGIS
$pythonPaths = @(
    (Join-Path $qgisPath "apps\Python313\python.exe"),
    (Join-Path $qgisPath "apps\Python312\python.exe"),
    (Join-Path $qgisPath "apps\Python311\python.exe"),
    (Join-Path $qgisPath "apps\Python39\python.exe"),
    (Join-Path $qgisPath "bin\python.exe")
)

$pythonExe = $null
foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        break
    }
}

if (-not $pythonExe) {
    Write-Host "ERROR: Could not find python.exe in QGIS installation" -ForegroundColor Red
    Write-Host "Checked paths:" -ForegroundColor Yellow
    foreach ($path in $pythonPaths) {
        Write-Host "  - $path" -ForegroundColor White
    }
    exit 1
}

Write-Host "Found Python at: $pythonExe" -ForegroundColor Green
Write-Host ""

# Check current Python version
Write-Host "Checking Python version..." -ForegroundColor Cyan
& $pythonExe --version
Write-Host ""

# Check current numpy version
Write-Host "Checking current numpy version..." -ForegroundColor Cyan
$numpyVersion = & $pythonExe -c "import numpy; print(numpy.__version__)" 2>$null
if ($numpyVersion) {
    Write-Host "Current numpy version: $numpyVersion" -ForegroundColor Yellow
    if ($numpyVersion -like "2.*") {
        Write-Host "WARNING: numpy 2.x detected - will downgrade to 1.x" -ForegroundColor Red
    }
} else {
    Write-Host "numpy not currently installed" -ForegroundColor Yellow
}
Write-Host ""

# Confirm with user
Write-Host "This will install/upgrade packages in QGIS's Python environment:" -ForegroundColor Yellow
Write-Host "  - numpy 1.26.4 (downgrade from 2.x if needed)" -ForegroundColor White
Write-Host "  - geopandas, pandas, networkx, scipy, shapely, etc." -ForegroundColor White
Write-Host ""
$response = Read-Host "Continue? (y/n)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}
Write-Host ""

# Upgrade pip first
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip
Write-Host ""

# Install numpy 1.x first (critical for compatibility)
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Installing numpy 1.26.4..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
& $pythonExe -m pip install "numpy==1.26.4" --force-reinstall
if (-not $?) {
    Write-Host "ERROR: Failed to install numpy 1.26.4" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Core dependencies (matching pyproject.toml but compatible versions)
Write-Host "Installing other dependencies..." -ForegroundColor Cyan
$dependencies = @(
    "geopandas==1.0.1",  # Compatible with numpy 1.x
    "pandas==2.2.3",     # Compatible with numpy 1.x
    "networkx==3.3",
    "scipy==1.13.1",     # Compatible with numpy 1.x
    "shapely>=2.0.0",
    "tqdm>=4.67.0",
    "folium",
    "plotly",
    "pydantic",
    "mapclassify",
    "matplotlib>=3.8.0"
)

foreach ($dep in $dependencies) {
    Write-Host "Installing $dep..." -ForegroundColor White
    & $pythonExe -m pip install $dep
    if (-not $?) {
        Write-Host "WARNING: Failed to install $dep" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Verify installations
Write-Host "Verifying installations..." -ForegroundColor Cyan
Write-Host ""

$verifyScript = @"
import sys
print(f"Python: {sys.version}")
print()

packages = ['numpy', 'pandas', 'geopandas', 'networkx', 'scipy', 'shapely', 'matplotlib']
for pkg in packages:
    try:
        mod = __import__(pkg)
        version = getattr(mod, '__version__', 'unknown')
        print(f"{pkg}: {version}")
    except ImportError as e:
        print(f"{pkg}: NOT INSTALLED ({e})")
"@

& $pythonExe -c $verifyScript

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Close QGIS completely if it's running" -ForegroundColor White
Write-Host "2. Restart QGIS" -ForegroundColor White
Write-Host "3. Open Python Console (Plugins > Python Console)" -ForegroundColor White
Write-Host "4. Run: import numpy; print(numpy.__version__)" -ForegroundColor White
Write-Host "5. Verify it shows 1.26.4 (not 2.x)" -ForegroundColor White
Write-Host ""
Write-Host "If QGIS still shows numpy 2.x:" -ForegroundColor Yellow
Write-Host "- Check for multiple QGIS installations" -ForegroundColor White
Write-Host "- Run this script again and select the correct QGIS path" -ForegroundColor White
Write-Host "- Check QGIS Python Console: import sys; print(sys.executable)" -ForegroundColor White
Write-Host ""
