# Register the Telegram bot as a logon Scheduled Task so it runs continuously
# (needed for the evening-question reminder) and survives reboots.
#   powershell -ExecutionPolicy Bypass -File scripts\schedule_bot.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
# Launch the bot hidden (no console) via the venv pythonw.exe. This requires the
# venv to be built on a real system Python (with pythonw.exe). NOTE: uv-managed
# CPython ships without pythonw.exe AND is not reachable from the Task Scheduler
# context, so the venv must be repointed to a stable system Python:
#   <system-python>\python.exe -m venv .venv --upgrade
$pyw = Join-Path $root ".venv\Scripts\pythonw.exe"
$action = New-ScheduledTaskAction -Execute $pyw `
  -Argument "-m walkingdev.cli bot" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -MultipleInstances IgnoreNew -RestartInterval (New-TimeSpan -Minutes 1) `
  -RestartCount 5 -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "TheWalkingDev-Bot" -Action $action `
  -Trigger $trigger -Settings $settings `
  -Description "Bot Telegram (onboarding + questions du soir)" -Force | Out-Null
Start-ScheduledTask -TaskName "TheWalkingDev-Bot"
Write-Host "Bot planifie (au logon) et demarre." -ForegroundColor Green
