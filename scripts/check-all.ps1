param(
  [switch]$SkipBackend,
  [switch]$SkipFrontend,
  [switch]$SkipMobile,
  [switch]$ReleaseMobile
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$flutter = Join-Path $env:USERPROFILE "Desktop\flutter\flutter\bin\flutter.bat"
$dart = Join-Path $env:USERPROFILE "Desktop\flutter\flutter\bin\dart.bat"

function Step($Name, [scriptblock]$Command) {
  Write-Host ""
  Write-Host "==> $Name" -ForegroundColor Cyan
  & $Command
}

if (-not $SkipBackend) {
  Step "Backend tests (mock provider)" {
    Push-Location (Join-Path $root "backend")
    try {
      $env:LLM_PROVIDER = "mock"
      & ".\.venv\Scripts\python.exe" -m pytest
    } finally {
      Pop-Location
    }
  }
}

if (-not $SkipFrontend) {
  Step "Frontend typecheck" {
    Push-Location (Join-Path $root "frontend")
    try {
      npm.cmd run typecheck
    } finally {
      Pop-Location
    }
  }

  Step "Frontend production build" {
    Push-Location (Join-Path $root "frontend")
    try {
      npm.cmd run build
    } finally {
      Pop-Location
    }
  }
}

if (-not $SkipMobile) {
  Step "Mobile format check" {
    Push-Location (Join-Path $root "mobile")
    try {
      & $dart format --set-exit-if-changed lib test
    } finally {
      Pop-Location
    }
  }

  Step "Mobile analyze" {
    Push-Location (Join-Path $root "mobile")
    try {
      & $flutter analyze
    } finally {
      Pop-Location
    }
  }

  Step "Mobile tests" {
    Push-Location (Join-Path $root "mobile")
    try {
      & $flutter test
    } finally {
      Pop-Location
    }
  }

  Step "Mobile debug APK build" {
    Push-Location (Join-Path $root "mobile")
    try {
      & $flutter build apk --debug --dart-define=API_BASE_URL=http://10.0.2.2:8000
    } finally {
      Pop-Location
    }
  }

  if ($ReleaseMobile) {
    Step "Mobile release APK build" {
      Push-Location (Join-Path $root "mobile")
      try {
        & $flutter build apk --release --dart-define=API_BASE_URL=http://10.0.2.2:8000
      } finally {
        Pop-Location
      }
    }
  }
}

Write-Host ""
Write-Host "All selected checks passed." -ForegroundColor Green
