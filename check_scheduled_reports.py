#!/usr/bin/env python
"""
Script to check for scheduled reports that need to be sent.
This script can be scheduled to run periodically using a task scheduler.

Example usage with Windows Task Scheduler:
- Program/script: python
- Arguments: C:\path\to\check_scheduled_reports.py
- Start in: C:\path\to\AutoDealerBDC
"""
import os
import sys
from app import create_app
from app.reports.report_scheduler import ReportScheduler

def main():
    """Check for scheduled reports and send them if needed."""
    print(f"[{datetime.now()}] Checking for scheduled reports...")
    
    # Create the application context
    app = create_app()
    with app.app_context():
        try:
            ReportScheduler.check_and_send_reports()
            print(f"[{datetime.now()}] Scheduled reports check completed successfully.")
            return 0
        except Exception as e:
            print(f"[{datetime.now()}] Error checking scheduled reports: {str(e)}")
            return 1

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
