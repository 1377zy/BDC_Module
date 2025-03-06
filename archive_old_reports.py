#!/usr/bin/env python
"""
Script to archive old report PDFs to save disk space.
This script can be scheduled to run periodically using a task scheduler.

Example usage with Windows Task Scheduler:
- Program/script: python
- Arguments: C:\path\to\archive_old_reports.py
- Start in: C:\path\to\AutoDealerBDC
"""
import os
import sys
import shutil
import zipfile
from datetime import datetime, timedelta
from app import create_app
from app.models import ScheduledReport
from app.extensions import db

def main():
    """Archive old report PDFs that are older than 90 days."""
    print(f"[{datetime.now()}] Archiving old report PDFs...")
    
    # Create the application context
    app = create_app()
    with app.app_context():
        try:
            # Create archive directory if it doesn't exist
            archive_dir = os.path.join(app.instance_path, 'report_archives')
            os.makedirs(archive_dir, exist_ok=True)
            
            # Get the path to the reports directory
            reports_dir = os.path.join(app.instance_path, 'reports')
            if not os.path.exists(reports_dir):
                print(f"[{datetime.now()}] Reports directory does not exist: {reports_dir}")
                return 0
            
            # Calculate the cutoff date (90 days ago)
            cutoff_date = datetime.now() - timedelta(days=90)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # Create a zip file for the archive
            archive_name = f"report_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            archive_path = os.path.join(archive_dir, archive_name)
            
            # Find old report PDFs
            archived_files = []
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(reports_dir):
                    for file in files:
                        if file.endswith('.pdf'):
                            file_path = os.path.join(root, file)
                            file_mtime = os.path.getmtime(file_path)
                            
                            # Check if the file is older than the cutoff date
                            if file_mtime < cutoff_timestamp:
                                # Add the file to the zip archive
                                arcname = os.path.relpath(file_path, reports_dir)
                                zipf.write(file_path, arcname)
                                archived_files.append(file_path)
            
            # Delete the archived files
            for file_path in archived_files:
                os.remove(file_path)
            
            print(f"[{datetime.now()}] Archived {len(archived_files)} old report PDFs to {archive_path}")
            
            # Update the database to mark archived reports
            if archived_files:
                # Extract report IDs from filenames (assuming format: report_<id>_<timestamp>.pdf)
                report_ids = []
                for file_path in archived_files:
                    filename = os.path.basename(file_path)
                    parts = filename.split('_')
                    if len(parts) >= 2 and parts[0] == 'report' and parts[1].isdigit():
                        report_ids.append(int(parts[1]))
                
                # Update the reports in the database
                if report_ids:
                    reports = ScheduledReport.query.filter(ScheduledReport.id.in_(report_ids)).all()
                    for report in reports:
                        report.archived = True
                        report.archive_path = archive_path
                    db.session.commit()
                    print(f"[{datetime.now()}] Updated {len(reports)} reports in the database as archived.")
            
            return 0
        except Exception as e:
            print(f"[{datetime.now()}] Error archiving old reports: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
