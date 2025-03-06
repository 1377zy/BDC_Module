#!/bin/bash
# Script to set up a cron job for the BDC Module's scheduled reports
# Run this script with appropriate permissions

# Get the absolute path to the project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)
SCRIPT_PATH="$PROJECT_DIR/check_scheduled_reports.py"

# Create a temporary file for the crontab
TEMP_CRON=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null

# Check if the cron job already exists
if grep -q "check_scheduled_reports.py" "$TEMP_CRON"; then
    echo "Cron job for scheduled reports already exists."
else
    # Add the new cron job to run daily at 6 AM
    echo "0 6 * * * cd $PROJECT_DIR && $PYTHON_PATH $SCRIPT_PATH >> $PROJECT_DIR/logs/scheduled_reports.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    echo "Cron job for scheduled reports has been added successfully."
    echo "The job will run daily at 6:00 AM."
fi

# Clean up the temporary file
rm "$TEMP_CRON"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"
touch "$PROJECT_DIR/logs/scheduled_reports.log"
echo "Log file created at $PROJECT_DIR/logs/scheduled_reports.log"
