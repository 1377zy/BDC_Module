@echo off
REM Batch file to run the archive_old_reports.py script
REM This can be used with Windows Task Scheduler

echo Archiving old reports at %date% %time%
cd /d %~dp0
python archive_old_reports.py
echo Old reports archiving completed at %date% %time%
