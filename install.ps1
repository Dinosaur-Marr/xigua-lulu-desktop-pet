param(
    [string]$DshHome = $(if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $env:USERPROFILE '.dsh' }),
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Profile = 'desktop',
    [switch]$DryRun,
    [string]$Restore
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js >=22.12.0 is required. Install Node.js from nodejs.org, then retry.' }
& node -e 'const [a,b]=process.versions.node.split(".").map(Number);if(a<22||(a===22&&b<12))process.exit(1)'
if ($LASTEXITCODE -ne 0) { throw 'Node.js >=22.12.0 is required.' }
& node (Join-Path $PSScriptRoot 'install.mjs') --verify
if ($LASTEXITCODE -ne 0) { throw 'Package verification failed.' }
$plugin = Join-Path $DshHome "profiles\$Profile\node_modules\dsh-pet\package.json"
if (-not $Restore -and -not (Test-Path -LiteralPath $plugin)) {
    if ($DryRun) { throw 'dsh-pet is not installed. Dry-run did not change anything.' }
    if (-not (Get-Command dsh -ErrorAction SilentlyContinue)) { throw 'DeepSeek Harness CLI (dsh) is required. Open a Harness terminal or add its CLI to PATH.' }
    $previousDshHome = $env:DSH_HOME
    try {
        $env:DSH_HOME = $DshHome
        & dsh plugin --profile $Profile add 'dsh-pet@0.3.7'
        if ($LASTEXITCODE -ne 0) { throw 'dsh-pet installation failed.' }
    } finally { $env:DSH_HOME = $previousDshHome }
    if (-not (Test-Path -LiteralPath $plugin)) { throw 'Plugin was not found in the selected profile. Check DshHome and Profile.' }
}
$installArgs = @((Join-Path $PSScriptRoot 'install.mjs'), '--dsh-home', $DshHome, '--profile', $Profile)
if ($DryRun) { $installArgs += '--dry-run' }
if ($Restore) { $installArgs += @('--restore', $Restore) }
& node @installArgs
if ($LASTEXITCODE -ne 0) { throw 'Installation or restore failed; see the message above.' }
