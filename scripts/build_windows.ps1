Param(
  [ValidateSet('zip','exe','all')]
  [string]$Mode = 'all',
  [switch]$UseVendor,          # bundle vendor/tesseract and vendor/poppler into the build outputs
  [switch]$MakeInstaller,      # run Inno Setup when available
  [switch]$SignArtifacts,      # sign BankCSV.exe (and installer) with signtool
  [string]$CertificatePath,
  [string]$CertificatePassword,
  [string]$TimestampUrl = 'http://timestamp.digicert.com',
  [string]$PythonExe
)

$ErrorActionPreference = 'Stop'
$scriptPath = $MyInvocation.MyCommand.Path
Write-Host "==> Using build script: $scriptPath"
$root = (Resolve-Path "$PSScriptRoot\..\").Path
$vendorRoot = Join-Path $root 'vendor'
Set-Location $root
$python = if ($PythonExe) { (Resolve-Path $PythonExe).Path } else { (Get-Command python).Source }

function Say($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

function Ensure-Tool($name, $args) {
  try { & $name $args | Out-Null } catch { throw "Required tool '$name' not found in PATH." }
}

function Vendor-Path([string]$name) {
  return Join-Path $vendorRoot $name
}

function Test-VendorReady([string]$name) {
  switch ($name) {
    'tesseract' { return Test-Path (Join-Path (Vendor-Path 'tesseract') 'tesseract.exe') }
    'poppler' { return Test-Path (Join-Path (Vendor-Path 'poppler') 'bin\pdftoppm.exe') }
    default { return $false }
  }
}

function Copy-VendorTree([string]$source, [string]$destination) {
  if (-not (Test-Path $source)) {
    throw "Vendor source '$source' not found."
  }
  if (Test-Path $destination) {
    Remove-Item $destination -Recurse -Force
  }
  New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
  Say "Copying $source -> $destination"
  Copy-Item -Path $source -Destination $destination -Recurse -Force
}

function Install-TesseractVendor {
  Say 'Installing Tesseract OCR via Chocolatey'
  Ensure-Tool 'choco' '--version'
  choco install tesseract --yes --no-progress | Out-Null
  $programFiles = ${env:ProgramFiles}
  $source = Join-Path $programFiles 'Tesseract-OCR'
  if (-not (Test-Path $source)) {
    throw "Tesseract installation not found at $source. Install it manually and rerun."
  }
  Copy-VendorTree $source (Vendor-Path 'tesseract')
}

function Install-PopplerVendor {
  Say 'Installing Poppler via Chocolatey'
  Ensure-Tool 'choco' '--version'
  choco install poppler --yes --no-progress | Out-Null
  $candidates = @()
  $programFiles = ${env:ProgramFiles}
  if ($programFiles -and (Test-Path $programFiles)) {
    $candidates += Get-ChildItem -Path $programFiles -Filter 'poppler*' -Directory -ErrorAction SilentlyContinue
  }
  $chocoTools = Join-Path ${env:ChocolateyInstall} 'lib\poppler\tools'
  if ($chocoTools -and (Test-Path $chocoTools)) {
    $candidates += Get-ChildItem -Path $chocoTools -Directory -ErrorAction SilentlyContinue
  }
  $sourceDir = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $sourceDir) {
    throw "Unable to locate Poppler installation. Install manually and rerun."
  }
  Copy-VendorTree $sourceDir.FullName (Vendor-Path 'poppler')
}

function Ensure-VendorBinaries {
  if (-not $UseVendor) {
    return
  }
  $needsTesseract = -not (Test-VendorReady 'tesseract')
  $needsPoppler = -not (Test-VendorReady 'poppler')
  if (-not ($needsTesseract -or $needsPoppler)) {
    Say 'Vendor binaries already present.'
    return
  }
  if ($needsTesseract) { Install-TesseractVendor }
  if ($needsPoppler) { Install-PopplerVendor }
}

function Validate-SigningInputs {
  if (-not $SignArtifacts) { return }
  if (-not (Test-Path $CertificatePath)) {
    throw "CertificatePath '$CertificatePath' not found."
  }
  if (-not $TimestampUrl) {
    throw 'TimestampUrl is required when SignArtifacts is enabled.'
  }
  Ensure-Tool 'signtool.exe' '-?'
}

function Sign-File($path) {
  if (-not $SignArtifacts) { return }
  if (-not (Test-Path $path)) {
    throw "Unable to sign '$path' because it does not exist."
  }
  Say "Signing $path"
  $args = @(
    'sign',
    '/fd', 'SHA256',
    '/tr', $TimestampUrl,
    '/td', 'SHA256',
    '/f', $CertificatePath
  )
  if ($CertificatePassword) {
    $args += @('/p', $CertificatePassword)
  }
  $args += $path
  & signtool.exe @args | Write-Host
}

function Build-Frontend {
  Say 'Building frontend (Vite)'
  Ensure-Tool 'npm' '--version'
  Push-Location "$root\frontend"
  try {
    if (Test-Path 'package-lock.json') {
      npm ci
    } else {
      npm install
    }
    npm run build
  } finally {
    Pop-Location
  }
}

function Build-Zip {
  Say 'Preparing ZIP release'
  $previous = $env:SKIP_FRONTEND_BUILD
  $env:SKIP_FRONTEND_BUILD = '1'
  try {
    & $python "$root\scripts\prepare_windows_release.py"
  } finally {
    if ($null -ne $previous) {
      $env:SKIP_FRONTEND_BUILD = $previous
    } else {
      Remove-Item Env:SKIP_FRONTEND_BUILD -ErrorAction SilentlyContinue
    }
  }
}

function Build-Exe {
  Say 'Building Windows executable with PyInstaller'
  & $python --version
  & $python -m pip install --upgrade pip | Out-Null
  & $python -m pip install pyinstaller | Out-Null
  & $python -m pip install -r (Join-Path $root 'backend\requirements.txt') | Out-Null
  if ($UseVendor) {
    Say 'Bundling vendor binaries into the EXE'
  } else {
    Write-Host 'Note: Tesseract/Poppler will need to be installed on target machines.'
  }
  $specPath = Join-Path $root 'packaging\windows\bank_csv.spec'
  $pyinstallerCmd = @($python, '-m', 'PyInstaller', $specPath, '--noconfirm')
  Say "Invoking PyInstaller via: $($pyinstallerCmd -join ' ')"
  & $python -m PyInstaller $specPath --noconfirm
  $exePath = Join-Path $root 'dist\BankCSV\BankCSV.exe'
  if ($SignArtifacts) { Sign-File $exePath }
  Write-Host "Built: $exePath"
}

function Build-Installer {
  $iscc = Get-Command iscc -ErrorAction SilentlyContinue
  if (-not $iscc) {
    Write-Warning 'Inno Setup (iscc) not found in PATH; skipping installer.'
    return
  }
  Say 'Building Inno Setup installer'
  & iscc "$root\packaging\windows\installer.iss"
  $installerPath = Join-Path $root 'release\windows\BankCSV-Setup.exe'
  if ($SignArtifacts) { Sign-File $installerPath }
}

# Build workflow
Build-Frontend
Ensure-VendorBinaries
Validate-SigningInputs
if ($Mode -eq 'zip' -or $Mode -eq 'all') { Build-Zip }
if ($Mode -eq 'exe' -or $Mode -eq 'all') { Build-Exe }
if ($MakeInstaller) { Build-Installer }

Say 'Done.'
