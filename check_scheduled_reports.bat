@echo off
REM Batch file to run the check_scheduled_reports.py script
REM This can be used with Windows Task Scheduler

echo Running scheduled reports check at %date% %time%
cd /d %~dp0
python check_scheduled_reports.py
echo Scheduled reports check completed at %date% %time%
