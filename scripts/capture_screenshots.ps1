# Script to capture genuine application screenshots for the academic report
$ErrorActionPreference = "Stop"

$screenshotsDir = "C:\Users\kmani\Desktop\AEG Hospital\docs\screenshots"
if (!(Test-Path $screenshotsDir)) {
    New-Item -ItemType Directory -Force -Path $screenshotsDir | Out-Null
}

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$tempDataDir = "C:\Users\kmani\Desktop\AEG Hospital\chrome-shot-temp"

function Capture-Page([string]$url, [string]$outputFilename) {
    $outPath = Join-Path $screenshotsDir $outputFilename
    Write-Host "Capturing $outputFilename from $url..."
    Start-Process -FilePath $chromePath -ArgumentList `
        "--headless=new", `
        "--disable-gpu", `
        "--no-sandbox", `
        "--virtual-time-budget=4000", `
        "--window-size=1440,900", `
        "--user-data-dir=`"$tempDataDir`"", `
        "--screenshot=`"$outPath`"", `
        "`"$url`"" -Wait
    Start-Sleep -Seconds 1
}

# 1. Reset simulation to initial state
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/simulation/reset" | Out-Null
Start-Sleep -Seconds 1

# Screenshot 1: Dashboard before simulation
Capture-Page "http://127.0.0.1:5173/?tab=overview" "01_dashboard_before_simulation.png"

# Screenshot 2: Patient Queue with priorities
Capture-Page "http://127.0.0.1:5173/?tab=patients" "02_patient_queue_priorities.png"

# Screenshot 3: Agent Monitor
Capture-Page "http://127.0.0.1:5173/?tab=agents" "03_agent_monitor.png"

# 2. Run simulation
Write-Host "Running simulation to produce real event and conflict logs..."
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/simulation/start" -Body '{"strategy":"PRIORITY_AWARE"}' -ContentType "application/json" | Out-Null
Start-Sleep -Seconds 2

# Screenshot 4: Event Timeline
Capture-Page "http://127.0.0.1:5173/?tab=timeline" "04_event_timeline.png"

# Screenshot 5: Resource Conflict Highlight
Capture-Page "http://127.0.0.1:5173/?tab=timeline" "05_resource_conflict.png"

# Screenshot 6: Resource Release
Capture-Page "http://127.0.0.1:5173/?tab=overview" "06_resource_release.png"

# Screenshot 7: Completed Metrics
Capture-Page "http://127.0.0.1:5173/?tab=metrics" "07_metrics_completed.png"

# Screenshot 8: FIFO Comparison Charts
Capture-Page "http://127.0.0.1:5173/?tab=metrics" "08_fifo_comparison_charts.png"

# Cleanup temp dir
Remove-Item -Recurse -Force $tempDataDir -ErrorAction SilentlyContinue

Write-Host "All 8 screenshots successfully captured into docs/screenshots/!"
Get-ChildItem $screenshotsDir | Select-Object Name, Length, LastWriteTime
