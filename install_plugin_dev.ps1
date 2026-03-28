# install_plugin_dev.ps1
# Install D-CASCADE QGIS Plugin for Development
# Creates a symlink/junction from QGIS plugins directory to development directory
# Uses the 'dcascade-testing' QGIS profile

$ErrorActionPreference = "Stop"

$pluginName = "dcascade"
$profileName = "dcascade-testing"

# Get the development directory (where this script is located)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$devPath = Join-Path $scriptPath "qgis_plugin"

# QGIS plugins path for the specified profile
$qgisPluginsPath = "$env:APPDATA\QGIS\QGIS\profiles\$profileName\python\plugins\$pluginName"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "D-CASCADE QGIS Plugin Development Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Development path: $devPath" -ForegroundColor Yellow
Write-Host "QGIS profile: $profileName" -ForegroundColor Yellow
Write-Host "Plugin target: $qgisPluginsPath" -ForegroundColor Yellow
Write-Host ""

# Verify development directory exists
if (-not (Test-Path $devPath)) {
    Write-Host "ERROR: Development directory not found: $devPath" -ForegroundColor Red
    Write-Host "Please ensure you're running this script from the project root." -ForegroundColor Red
    exit 1
}

# Verify plugin files exist
$initFile = Join-Path $devPath "__init__.py"
$metadataFile = Join-Path $devPath "metadata.txt"

if (-not (Test-Path $initFile)) {
    Write-Host "WARNING: __init__.py not found in $devPath" -ForegroundColor Yellow
}

if (-not (Test-Path $metadataFile)) {
    Write-Host "WARNING: metadata.txt not found in $devPath" -ForegroundColor Yellow
}

# Check if symlink/junction already exists
if (Test-Path $qgisPluginsPath) {
    $existingItem = Get-Item $qgisPluginsPath -ErrorAction SilentlyContinue
    
    if ($existingItem.LinkType -eq "Junction" -or $existingItem.LinkType -eq "SymbolicLink") {
        Write-Host "Found existing junction/symlink at: $qgisPluginsPath" -ForegroundColor Yellow
        $response = Read-Host "Remove and recreate? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Remove-Item $qgisPluginsPath -Force -Recurse
            Write-Host "Removed existing link." -ForegroundColor Green
        } else {
            Write-Host "Aborted." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "WARNING: Directory exists at $qgisPluginsPath but is not a junction/symlink." -ForegroundColor Yellow
        $response = Read-Host "Remove and create junction? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Remove-Item $qgisPluginsPath -Force -Recurse
            Write-Host "Removed existing directory." -ForegroundColor Green
        } else {
            Write-Host "Aborted." -ForegroundColor Yellow
            exit 0
        }
    }
}

# Create directory structure if it doesn't exist
$pluginsDir = Split-Path $qgisPluginsPath -Parent
if (-not (Test-Path $pluginsDir)) {
    Write-Host "Creating plugins directory: $pluginsDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
}

# Check if profile directory exists
$profileDir = "$env:APPDATA\QGIS\QGIS3\profiles\$profileName"
if (-not (Test-Path $profileDir)) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "WARNING: QGIS profile '$profileName' does not exist!" -ForegroundColor Yellow
    Write-Host "Profile path: $profileDir" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can create this profile in QGIS:" -ForegroundColor Cyan
    Write-Host "1. Open QGIS" -ForegroundColor Cyan
    Write-Host "2. Settings -> User Profiles -> New Profile" -ForegroundColor Cyan
    Write-Host "3. Name it dcascade-testing" -ForegroundColor Cyan
    Write-Host ""
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

# Create junction (symlink for directories on Windows)
try {
    Write-Host "Creating junction link..." -ForegroundColor Cyan
    New-Item -ItemType Junction -Path $qgisPluginsPath -Target $devPath -Force | Out-Null
    Write-Host ""
    Write-Host "Success! Junction created successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "Setup complete:" -ForegroundColor Cyan
    Write-Host "  Source: $devPath" -ForegroundColor White
    Write-Host "  Target: $qgisPluginsPath" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Open QGIS with profile '$profileName'" -ForegroundColor White
    Write-Host "2. Go to Plugins Manage and Install Plugins" -ForegroundColor White
    Write-Host "3. Enable D-CASCADE plugin" -ForegroundColor White
    Write-Host "4. For rapid development, install Plugin Reloader plugin" -ForegroundColor White
    Write-Host "   (allows reloading plugin without restarting QGIS)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create junction: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "- Run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "- Check that target directory exists: $devPath" -ForegroundColor Yellow
    Write-Host "- Check that plugins directory exists: $pluginsDir" -ForegroundColor Yellow
    exit 1
}

