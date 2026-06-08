# Install Update Agent as a Windows Scheduled Task
# This script sets up the auto-update agent to run as a scheduled task

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Update Agent Installation (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "📁 Installation directory: $ScriptDir" -ForegroundColor Yellow

# Python executable path
$PythonExe = "python"
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonExe = "python3"
}

Write-Host "🐍 Using Python: $PythonExe" -ForegroundColor Yellow

# Task name
$TaskName = "GPU-Monitor-Update-Agent"

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "🗑️  Removing existing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "$ScriptDir\update_agent.py" `
    -WorkingDirectory $ScriptDir

# Create the trigger (run at startup and every hour)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

# Create the principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Create the settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Register the scheduled task
Write-Host "📋 Creating scheduled task..." -ForegroundColor Yellow
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Auto-update agent for GPU Monitor Dashboard" | Out-Null

# Start the task
Write-Host "🚀 Starting scheduled task..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Update agent installed and started!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view task status:" -ForegroundColor White
Write-Host "   Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "To view task history:" -ForegroundColor White
Write-Host "   Get-ScheduledTaskInfo -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop the task:" -ForegroundColor White
Write-Host "   Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "To start the task:" -ForegroundColor White
Write-Host "   Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "To remove the task:" -ForegroundColor White
Write-Host "   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "Log file location:" -ForegroundColor White
Write-Host "   $ScriptDir\update_agent.log" -ForegroundColor Gray
Write-Host ""
