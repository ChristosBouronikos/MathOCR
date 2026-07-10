# MathOCR Windows packager by Bouronikos Christos <chrisbouronikos@gmail.com>.
# Support development: https://paypal.me/christosbouronikos

$ErrorActionPreference = "Stop"
$compilerCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$compiler = $compilerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $compiler) {
    throw "Inno Setup 6 was not found. Install it before packaging MathOCR."
}

& $compiler "packaging\windows\MathOCR.iss"
if (-not (Test-Path "dist\MathOCR-Setup.exe")) {
    throw "Inno Setup did not create dist\MathOCR-Setup.exe"
}
Write-Host "Windows installer created: dist\MathOCR-Setup.exe"

