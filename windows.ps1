# ============================================================
#  cleanup_ollama_windows.ps1
#  Fully removes Ollama + all models + cleans system cache
#  Run as Administrator in PowerShell
#  Usage: Right-click → "Run with PowerShell as Administrator"
#         OR in PowerShell: .\cleanup_ollama_windows.ps1
# ============================================================


# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser 

# ── Require Admin ────────────────────────────────────────────
if (-NOT ([Security.Principal.WindowsPrincipal]
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host ""
    Write-Host "ERROR: Please run this script as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell → Run as Administrator" -ForegroundColor Yellow
    pause
    exit 1
}

# ── Helper ───────────────────────────────────────────────────
function Print-Step($msg) {
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "===================================================" -ForegroundColor Cyan
}

function Remove-ItemSafe($path) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
        Write-Host "  Deleted: $path" -ForegroundColor Green
    } else {
        Write-Host "  Not found (skip): $path" -ForegroundColor DarkGray
    }
}

function Get-FolderSize($path) {
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        return [math]::Round($size / 1MB, 2)
    }
    return 0
}

# ── Disk usage BEFORE ────────────────────────────────────────
Print-Step "Checking disk usage BEFORE cleanup"
$driveLetter = $env:SystemDrive
$diskBefore  = Get-PSDrive ($driveLetter.TrimEnd(':')) |
               Select-Object -ExpandProperty Free
Write-Host "  Free space before: $([math]::Round($diskBefore/1GB,2)) GB" -ForegroundColor Yellow


# ────────────────────────────────────────────────────────────
#  SECTION 1 — STOP OLLAMA PROCESS
# ────────────────────────────────────────────────────────────
Print-Step "Step 1 — Stopping Ollama process"

$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($ollamaProcess) {
    Stop-Process -Name "ollama" -Force
    Write-Host "  Ollama process stopped." -ForegroundColor Green
} else {
    Write-Host "  Ollama not running (skip)." -ForegroundColor DarkGray
}

# Also kill ollama app tray
Get-Process -Name "ollama app" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2


# ────────────────────────────────────────────────────────────
#  SECTION 2 — UNINSTALL OLLAMA APPLICATION
# ────────────────────────────────────────────────────────────
Print-Step "Step 2 — Uninstalling Ollama application"

# Method A: winget (works if installed via winget)
$wingetInstalled = Get-Command winget -ErrorAction SilentlyContinue
if ($wingetInstalled) {
    Write-Host "  Trying winget uninstall..." -ForegroundColor Yellow
    winget uninstall --id Ollama.Ollama --silent 2>$null
}

# Method B: Registry uninstall string (works for .exe installers)
$regPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
foreach ($regPath in $regPaths) {
    $app = Get-ItemProperty $regPath -ErrorAction SilentlyContinue |
           Where-Object { $_.DisplayName -like "*Ollama*" }
    if ($app -and $app.UninstallString) {
        Write-Host "  Found via registry: $($app.DisplayName)" -ForegroundColor Yellow
        $uninstallCmd = $app.UninstallString -replace '"', ''
        Start-Process -FilePath $uninstallCmd -ArgumentList "/S" -Wait -ErrorAction SilentlyContinue
        Write-Host "  Uninstalled via registry." -ForegroundColor Green
    }
}


# ────────────────────────────────────────────────────────────
#  SECTION 3 — REMOVE ALL OLLAMA FILES & FOLDERS
# ────────────────────────────────────────────────────────────
Print-Step "Step 3 — Removing Ollama files and model data"

# Model weights (the big files — can be 5–20 GB)
$modelSize = Get-FolderSize "$env:USERPROFILE\.ollama"
Write-Host "  Model data size: $modelSize MB" -ForegroundColor Yellow

Remove-ItemSafe "$env:USERPROFILE\.ollama"                    # models, manifests, blobs
Remove-ItemSafe "$env:APPDATA\Ollama"                         # app config
Remove-ItemSafe "$env:LOCALAPPDATA\Ollama"                    # local app data
Remove-ItemSafe "$env:LOCALAPPDATA\Programs\Ollama"           # installed binaries
Remove-ItemSafe "$env:PROGRAMFILES\Ollama"                    # if installed system-wide
Remove-ItemSafe "$env:PROGRAMFILES(X86)\Ollama"               # 32-bit install location
Remove-ItemSafe "$env:TEMP\ollama*"                           # temp files


# ────────────────────────────────────────────────────────────
#  SECTION 4 — REMOVE FROM PATH ENVIRONMENT VARIABLE
# ────────────────────────────────────────────────────────────
Print-Step "Step 4 — Cleaning Ollama from PATH"

# User PATH
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -like "*ollama*") {
    $cleanPath = ($userPath -split ";" |
                  Where-Object { $_ -notlike "*ollama*" }) -join ";"
    [Environment]::SetEnvironmentVariable("PATH", $cleanPath, "User")
    Write-Host "  Removed Ollama from User PATH." -ForegroundColor Green
} else {
    Write-Host "  Ollama not in User PATH (skip)." -ForegroundColor DarkGray
}

# System PATH
$sysPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($sysPath -like "*ollama*") {
    $cleanSysPath = ($sysPath -split ";" |
                     Where-Object { $_ -notlike "*ollama*" }) -join ";"
    [Environment]::SetEnvironmentVariable("PATH", $cleanSysPath, "Machine")
    Write-Host "  Removed Ollama from System PATH." -ForegroundColor Green
} else {
    Write-Host "  Ollama not in System PATH (skip)." -ForegroundColor DarkGray
}


# ────────────────────────────────────────────────────────────
#  SECTION 5 — CLEAN PYTHON & AI/ML CACHES
# ────────────────────────────────────────────────────────────
Print-Step "Step 5 — Cleaning Python / AI / ML caches"

# pip cache
Write-Host "  Clearing pip cache..." -ForegroundColor Yellow
pip cache purge 2>$null
pip3 cache purge 2>$null
Remove-ItemSafe "$env:LOCALAPPDATA\pip\Cache"

# HuggingFace model cache (sentence-transformers, embeddings etc.)
$hfSize = Get-FolderSize "$env:USERPROFILE\.cache\huggingface"
Write-Host "  HuggingFace cache size: $hfSize MB" -ForegroundColor Yellow
Remove-ItemSafe "$env:USERPROFILE\.cache\huggingface"

# PyTorch cache
$torchSize = Get-FolderSize "$env:USERPROFILE\.cache\torch"
Write-Host "  Torch cache size: $torchSize MB" -ForegroundColor Yellow
Remove-ItemSafe "$env:USERPROFILE\.cache\torch"

# Sentence-transformers cache
Remove-ItemSafe "$env:USERPROFILE\.cache\sentence_transformers"

# ChromaDB local data (if any)
Remove-ItemSafe "$env:USERPROFILE\.chroma"


# ────────────────────────────────────────────────────────────
#  SECTION 6 — GENERAL WINDOWS CACHE CLEANUP
# ────────────────────────────────────────────────────────────
Print-Step "Step 6 — General Windows cache cleanup"

# Windows Temp folders
Write-Host "  Clearing Windows Temp..." -ForegroundColor Yellow
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  Temp folders cleared." -ForegroundColor Green

# Windows Update cache (can be huge — safe to delete)
Write-Host "  Clearing Windows Update cache..." -ForegroundColor Yellow
Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" `
    -Recurse -Force -ErrorAction SilentlyContinue
Start-Service -Name wuauserv -ErrorAction SilentlyContinue
Write-Host "  Windows Update cache cleared." -ForegroundColor Green

# DNS cache
Write-Host "  Flushing DNS cache..." -ForegroundColor Yellow
ipconfig /flushdns | Out-Null
Write-Host "  DNS cache flushed." -ForegroundColor Green

# Windows Prefetch
Remove-Item "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue
Write-Host "  Prefetch cleared." -ForegroundColor Green

# Recycle Bin
Write-Host "  Emptying Recycle Bin..." -ForegroundColor Yellow
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Write-Host "  Recycle Bin emptied." -ForegroundColor Green

# Thumbnail cache
Remove-ItemSafe "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"

# Browser caches (common ones)
$browserCaches = @(
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:APPDATA\Mozilla\Firefox\Profiles\*\cache2"
)
foreach ($cache in $browserCaches) {
    Remove-ItemSafe $cache
}


# ────────────────────────────────────────────────────────────
#  SECTION 7 — RUN BUILT-IN DISK CLEANUP (SILENT)
# ────────────────────────────────────────────────────────────
Print-Step "Step 7 — Running Windows Disk Cleanup silently"

# Set cleanmgr flags for all standard categories
$regCleanup = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches"
$cleanupItems = @(
    "Active Setup Temp Folders", "BranchCache", "Downloaded Program Files",
    "GameNewsFiles", "GameStatisticsFiles", "GameUpdateFiles",
    "Internet Cache Files", "Memory Dump Files", "Offline Pages Files",
    "Old ChkDsk Files", "Previous Installations", "Recycle Bin",
    "Service Pack Cleanup", "Setup Log Files", "System error memory dump files",
    "System error minidump files", "Temporary Files", "Temporary Setup Files",
    "Thumbnail Cache", "Update Cleanup", "Upgrade Discarded Files",
    "Windows Defender", "Windows Error Reporting Archive Files",
    "Windows Error Reporting Queue Files", "Windows Error Reporting System Archive Files",
    "Windows Error Reporting System Queue Files", "Windows ESD installation files",
    "Windows Upgrade Log Files"
)
foreach ($item in $cleanupItems) {
    $path = "$regCleanup\$item"
    if (Test-Path $path) {
        Set-ItemProperty -Path $path -Name "StateFlags0064" -Value 2 -ErrorAction SilentlyContinue
    }
}
Write-Host "  Running cleanmgr (this may take a minute)..." -ForegroundColor Yellow
Start-Process cleanmgr -ArgumentList "/sagerun:64" -Wait -ErrorAction SilentlyContinue
Write-Host "  Disk Cleanup complete." -ForegroundColor Green


# ────────────────────────────────────────────────────────────
#  SECTION 8 — VERIFY OLLAMA IS GONE
# ────────────────────────────────────────────────────────────
Print-Step "Step 8 — Verification"

$ollamaBin    = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaFolder = Test-Path "$env:USERPROFILE\.ollama"
$ollamaApp    = Test-Path "$env:LOCALAPPDATA\Programs\Ollama"

if ($ollamaBin) {
    Write-Host "  WARNING: ollama command still found at $($ollamaBin.Source)" -ForegroundColor Red
} else {
    Write-Host "  ollama command: NOT FOUND (good)" -ForegroundColor Green
}

if ($ollamaFolder) {
    Write-Host "  WARNING: ~/.ollama folder still exists" -ForegroundColor Red
} else {
    Write-Host "  ~/.ollama folder: GONE (good)" -ForegroundColor Green
}

if ($ollamaApp) {
    Write-Host "  WARNING: Ollama app folder still exists" -ForegroundColor Red
} else {
    Write-Host "  Ollama app folder: GONE (good)" -ForegroundColor Green
}


# ── Disk usage AFTER ─────────────────────────────────────────
Print-Step "Disk usage AFTER cleanup"
$diskAfter = Get-PSDrive ($driveLetter.TrimEnd(':')) |
             Select-Object -ExpandProperty Free
$freedGB   = [math]::Round(($diskAfter - $diskBefore) / 1GB, 2)

Write-Host "  Free space after : $([math]::Round($diskAfter/1GB,2)) GB" -ForegroundColor Green
Write-Host "  Space freed       : $freedGB GB" -ForegroundColor Cyan


# ────────────────────────────────────────────────────────────
#  DONE
# ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Cleanup complete!" -ForegroundColor Green
Write-Host "  Restart your PC to finish clearing" -ForegroundColor Yellow
Write-Host "  memory-mapped files and DLL locks." -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

pause