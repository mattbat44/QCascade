# install_basic_user.ps1
# One-click installer for non-developer users.
# Installs the D-CASCADE plugin into the default QGIS profile and installs
# required Python packages into the detected QGIS Python environment.

[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host "" 
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
}

function Find-QgisPython {
    $candidateQgisRoots = @(
        "C:\Program Files\QGIS 3.40",
        "C:\Program Files\QGIS 3.38",
        "C:\Program Files\QGIS 3.34",
        "C:\Program Files\QGIS*",
        "C:\OSGeo4W64",
        "C:\OSGeo4W"
    )

    $roots = @()
    foreach ($pattern in $candidateQgisRoots) {
        if ($pattern.Contains("*")) {
            $expanded = Get-ChildItem -Path $pattern -Directory -ErrorAction SilentlyContinue
            if ($expanded) {
                $roots += $expanded.FullName
            }
        } elseif (Test-Path $pattern) {
            $roots += $pattern
        }
    }

    $roots = $roots | Select-Object -Unique

    foreach ($root in $roots) {
        $pythonCandidates = @(
            (Join-Path $root "apps\Python313\python.exe"),
            (Join-Path $root "apps\Python312\python.exe"),
            (Join-Path $root "apps\Python311\python.exe"),
            (Join-Path $root "apps\Python310\python.exe"),
            (Join-Path $root "apps\Python39\python.exe"),
            (Join-Path $root "bin\python.exe")
        )

        foreach ($pythonPath in $pythonCandidates) {
            if (Test-Path $pythonPath) {
                return $pythonPath
            }
        }
    }

    return $null
}

function Install-PluginFiles {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $sourceDir = Join-Path $scriptRoot "qgis_plugin"

    if (-not (Test-Path $sourceDir)) {
        throw "Plugin source directory was not found: $sourceDir"
    }

    $pluginsRoot = Join-Path $env:APPDATA "QGIS\QGIS3\profiles\default\python\plugins"
    $targetDir = Join-Path $pluginsRoot "dcascade"

    Write-Host "Plugin source: $sourceDir" -ForegroundColor Yellow
    Write-Host "Plugin target: $targetDir" -ForegroundColor Yellow

    if (-not (Test-Path $pluginsRoot)) {
        New-Item -ItemType Directory -Path $pluginsRoot -Force | Out-Null
    }

    if (Test-Path $targetDir) {
        if (-not $Force) {
            $answer = Read-Host "Existing plugin installation found. Replace it? (y/n)"
            if ($answer -notin @("y", "Y")) {
                throw "Installation cancelled by user."
            }
        }

        Remove-Item -Path $targetDir -Recurse -Force
    }

    Copy-Item -Path $sourceDir -Destination $targetDir -Recurse -Force

    Write-Host "Plugin files installed successfully." -ForegroundColor Green
}

function Install-Dependencies {
    param([Parameter(Mandatory = $true)][string]$PythonExe)

    $dependencies = @(
        "numpy==1.26.4",
        "geopandas==1.0.1",
        "pandas==2.2.3",
        "networkx==3.3",
        "scipy==1.13.1",
        "shapely>=2.0.0",
        "matplotlib>=3.8.0",
        "tqdm>=4.67.0",
        "folium",
        "plotly",
        "pydantic",
        "mapclassify",
        "openpyxl>=3.1.5"
    )

    Write-Host "Using QGIS Python: $PythonExe" -ForegroundColor Yellow

    & $PythonExe -m pip install --upgrade pip

    foreach ($dep in $dependencies) {
        Write-Host "Installing $dep ..." -ForegroundColor White
        & $PythonExe -m pip install $dep
    }

    Write-Host "Dependency installation finished." -ForegroundColor Green
}

function Fetch-ModelFiles {
    param([Parameter(Mandatory = $true)][string]$PythonExe)

    $scriptRoot = Split-Path -Parent $MyInvocation.ScriptName
    if (-not $scriptRoot) { $scriptRoot = $PSScriptRoot }
    $fetchScript = Join-Path $scriptRoot "fetch_dcascade_model.py"

    if (-not (Test-Path $fetchScript)) {
        throw "fetch_dcascade_model.py not found at: $fetchScript"
    }

    Write-Host "Fetching upstream model files from dcascade-py v2.0.0 …" -ForegroundColor Yellow
    & $PythonExe $fetchScript
    if ($LASTEXITCODE -ne 0) {
        throw "fetch_dcascade_model.py failed (exit code $LASTEXITCODE)."
    }
    Write-Host "Model files ready." -ForegroundColor Green
}

try {
    Write-Section "D-CASCADE Basic User Installer"

    $qgisProcesses = Get-Process -Name "qgis*" -ErrorAction SilentlyContinue
    if ($qgisProcesses) {
        throw "Please close QGIS before installation, then run this script again."
    }

    Write-Section "Step 1/4 - Detect QGIS Python"
    $pythonExe = Find-QgisPython

    if (-not $pythonExe) {
        throw "Could not find QGIS Python automatically. Install QGIS first, then re-run this script."
    }

    Write-Section "Step 2/4 - Install Python Dependencies"

    Install-Dependencies -PythonExe $pythonExe

    Write-Section "Step 3/4 - Fetch Upstream Model Files"
    Fetch-ModelFiles -PythonExe $pythonExe

    Write-Section "Step 4/4 - Install Plugin Files"
    Install-PluginFiles

    Write-Section "Installation Complete"
    Write-Host "D-CASCADE is installed for the default QGIS profile." -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Start QGIS" -ForegroundColor White
    Write-Host "2. Open Plugins -> Manage and Install Plugins" -ForegroundColor White
    Write-Host "3. Enable D-CASCADE" -ForegroundColor White
} catch {
    Write-Host "" 
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
