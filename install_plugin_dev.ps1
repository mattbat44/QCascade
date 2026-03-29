[CmdletBinding()]
param(
    [string]$ProfileName = "dcascade-testing",
    [switch]$SkipDependencies
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

    Write-Host "Fetching upstream model files from dcascade-py v2.0.0 ..." -ForegroundColor Yellow
    & $PythonExe $fetchScript
    if ($LASTEXITCODE -ne 0) {
        throw "fetch_dcascade_model.py failed (exit code $LASTEXITCODE)."
    }
    Write-Host "Model files ready." -ForegroundColor Green
}

try {
    $pluginName = "dcascade"
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $devPath = Join-Path $scriptPath "qgis_plugin"
    $qgisPluginsPath = Join-Path $env:APPDATA "QGIS\QGIS3\profiles\$ProfileName\python\plugins\$pluginName"
    $pluginsDir = Split-Path $qgisPluginsPath -Parent
    $profileDir = Join-Path $env:APPDATA "QGIS\QGIS3\profiles\$ProfileName"

    Write-Section "D-CASCADE Development Installer"
    Write-Host "Development path: $devPath" -ForegroundColor Yellow
    Write-Host "QGIS profile: $ProfileName" -ForegroundColor Yellow
    Write-Host "Plugin target: $qgisPluginsPath" -ForegroundColor Yellow

    if (-not (Test-Path $devPath)) {
        throw "Development directory not found: $devPath"
    }

    $qgisProcesses = Get-Process -Name "qgis*" -ErrorAction SilentlyContinue
    if ($qgisProcesses) {
        throw "Please close QGIS before installation, then run this script again."
    }

    if (-not (Test-Path $profileDir)) {
        Write-Host "" 
        Write-Host "WARNING: QGIS profile '$ProfileName' does not exist yet." -ForegroundColor Yellow
        Write-Host "Create it in QGIS via Settings -> User Profiles -> New Profile." -ForegroundColor Yellow
        $response = Read-Host "Continue anyway? (y/n)"
        if ($response -notin @("y", "Y")) {
            Write-Host "Aborted." -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Section "Step 1/3 - Link Plugin Source"
    if (-not (Test-Path $pluginsDir)) {
        New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
    }

    if (Test-Path $qgisPluginsPath) {
        $existingItem = Get-Item $qgisPluginsPath -ErrorAction SilentlyContinue
        if ($existingItem.LinkType -eq "Junction" -or $existingItem.LinkType -eq "SymbolicLink") {
            Write-Host "Found existing junction/symlink at: $qgisPluginsPath" -ForegroundColor Yellow
            $response = Read-Host "Remove and recreate? (y/n)"
            if ($response -notin @("y", "Y")) {
                Write-Host "Aborted." -ForegroundColor Yellow
                exit 0
            }
        } else {
            Write-Host "WARNING: Directory exists at $qgisPluginsPath but is not a junction/symlink." -ForegroundColor Yellow
            $response = Read-Host "Remove and create junction? (y/n)"
            if ($response -notin @("y", "Y")) {
                Write-Host "Aborted." -ForegroundColor Yellow
                exit 0
            }
        }
        Remove-Item $qgisPluginsPath -Force -Recurse
    }

    New-Item -ItemType Junction -Path $qgisPluginsPath -Target $devPath -Force | Out-Null
    Write-Host "Plugin junction created." -ForegroundColor Green

    if (-not $SkipDependencies) {
        Write-Section "Step 2/3 - Install Python Dependencies"
        $pythonExe = Find-QgisPython
        if (-not $pythonExe) {
            throw "Could not find QGIS Python automatically. Install QGIS first, then re-run this script."
        }
        Install-Dependencies -PythonExe $pythonExe

        Write-Section "Step 3/3 - Fetch Upstream Model Files"
        Fetch-ModelFiles -PythonExe $pythonExe
    } else {
        Write-Section "Step 2/3 - Skipped"
        Write-Host "Dependency installation skipped by request." -ForegroundColor Yellow
        Write-Section "Step 3/3 - Skipped"
        Write-Host "Model fetch skipped by request." -ForegroundColor Yellow
    }

    Write-Section "Installation Complete"
    Write-Host "D-CASCADE dev setup is ready for profile '$ProfileName'." -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Open QGIS with profile '$ProfileName'" -ForegroundColor White
    Write-Host "2. Enable D-CASCADE in Plugins -> Manage and Install Plugins" -ForegroundColor White
    Write-Host "3. Optional: install Plugin Reloader for fast plugin reloads" -ForegroundColor White
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

