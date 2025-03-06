# PowerShell script to set up a scheduled task for the BDC Module's scheduled reports
# Run this script as an administrator

# Get the current directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = "python"
$scriptToRun = "$scriptPath\check_scheduled_reports.py"

# Create a new scheduled task action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptToRun -WorkingDirectory $scriptPath

# Create a trigger to run the task daily at 6 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 6am

# Set the task settings
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Create the scheduled task
$taskName = "BDC_Module_Scheduled_Reports"
$description = "Checks for and sends scheduled reports for the Auto Dealership BDC Module"

# Register the scheduled task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $description -RunLevel Highest -Force

Write-Host "Scheduled task '$taskName' has been created successfully."
Write-Host "The task will run daily at 6:00 AM."
Write-Host "You can modify the schedule in Task Scheduler if needed."
