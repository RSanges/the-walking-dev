# Register the nightly generation as a Windows Scheduled Task.
#   powershell -ExecutionPolicy Bypass -File scripts\schedule_task.ps1 -At 05:30
param([string]$At = "05:30")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
# Call the venv Python directly. We avoid `uv run` here because Windows
# Application Control can intermittently block uv.exe, which would silently
# break the unattended 05:30 run.
$py = Join-Path $root ".venv\Scripts\python.exe"
$action = New-ScheduledTaskAction -Execute $py `
  -Argument "-m walkingdev.cli nightly" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -DontStopOnIdleEnd -WakeToRun
Register-ScheduledTask -TaskName "TheWalkingDev-Nightly" -Action $action `
  -Trigger $trigger -Settings $settings -Description "Genere le podcast quotidien" -Force
Write-Host "Tache planifiee 'TheWalkingDev-Nightly' creee a $At." -ForegroundColor Green
