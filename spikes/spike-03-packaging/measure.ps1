# measure.ps1 -- size and cold-start measurement for the bundled probe.
#
# Deviation from the plan: the plan's original version force-kills the
# process (Stop-Process -Force / TerminateProcess) after a fixed sleep.
# On this machine that reliably LOST the frozen exe's "COLD_START_MS=..."
# stdout line: CPython fully-buffers stdout when it is not attached to a
# real console (true for any redirected/piped stdout, frozen or not), and
# TerminateProcess gives the process no chance to flush that buffer before
# it dies -- so in_process_cold_start_ms came back $null every single time,
# even though the app was working correctly. This was confirmed to be a
# stdout-flush timing issue, not an app/libclang bug, by (a) observing
# MainWindowTitle = 'Spike 03 -- Packaging Probe' and Responding = $true
# while stdout was still empty, and (b) reproducing the identical
# silent-stdout behavior when running the UNBUNDLED `python.exe app.py`
# under the same Start-Process redirection without -u/PYTHONUNBUFFERED.
#
# Fix: request a graceful close (CloseMainWindow -> WM_CLOSE) so the app's
# own sys.exit()/interpreter shutdown flushes stdio normally, and only
# fall back to a hard kill if it doesn't exit in time. PYTHONUNBUFFERED=1
# is also set as defense-in-depth in case the fallback hard-kill path is
# ever hit.
$ErrorActionPreference = "Stop"
$distDir = "dist/spike03_probe"
$exe = Join-Path $distDir "spike03_probe.exe"

if (-not (Test-Path $exe)) {
    throw "Build first: python -m PyInstaller packaging.spec --noconfirm"
}

$sizeBytes = (Get-ChildItem -Recurse $distDir | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($sizeBytes / 1MB, 1)

$env:PYTHONUNBUFFERED = "1"
$launchStart = Get-Date
$proc = Start-Process -FilePath $exe -PassThru -RedirectStandardOutput "stdout.tmp" -RedirectStandardError "stderr.tmp"
Start-Sleep -Milliseconds 1500
$launchWallMs = ((Get-Date) - $launchStart).TotalMilliseconds

# Graceful close so the already-printed, buffered COLD_START_MS line
# flushes via normal interpreter shutdown; hard-kill only as a fallback.
$closedGracefully = $false
try {
    if (-not $proc.HasExited) {
        $proc.CloseMainWindow() | Out-Null
        $closedGracefully = $proc.WaitForExit(5000)
    }
} catch {
    $closedGracefully = $false
}
if (-not $proc.HasExited) {
    $proc | Stop-Process -Force -ErrorAction SilentlyContinue
}

$stdout = Get-Content "stdout.tmp" -Raw -ErrorAction SilentlyContinue
$inProcessMs = $null
if ($stdout -match "COLD_START_MS=([\d.]+)") {
    $inProcessMs = [double]$Matches[1]
}
Remove-Item "stdout.tmp" -ErrorAction SilentlyContinue
Remove-Item "stderr.tmp" -ErrorAction SilentlyContinue

$result = @{
    dist_size_mb = $sizeMB
    process_launch_wall_ms = [math]::Round($launchWallMs, 1)
    in_process_cold_start_ms = $inProcessMs
    closed_gracefully = $closedGracefully
    measured_at_utc = (Get-Date).ToUniversalTime().ToString("o")
}
$result | ConvertTo-Json | Out-File -Encoding utf8 "measurements.json"
Get-Content "measurements.json"
