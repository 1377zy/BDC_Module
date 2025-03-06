#!/usr/bin/env python
"""
Test script for scheduled reports functionality.
This script creates a test scheduled report and sends it immediately.
"""
import os
import sys
from datetime import datetime, timedelta
from app import create_app, db
from app.models import ScheduledReport, User

def main():
    """Create and send a test scheduled report."""
    print(f"[{datetime.now()}] Testing scheduled reports functionality...")
    
    # Create the application context
    app = create_app()
    with app.app_context():
        try:
            # Find an admin user to assign the report to
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                print("No admin user found. Please create an admin user first.")
                return 1
            
            # Create a test scheduled report
            report = ScheduledReport(
                name="Test Report",
                report_type="inventory",
                frequency="daily",
                time_of_day=datetime.now().time(),
                recipients=admin_user.email,
                format="pdf",
                include_charts=True,
                date_range="last_30_days",
                active=True,
                created_by_id=admin_user.id
            )
            
            db.session.add(report)
            db.session.commit()
            print(f"Created test report with ID: {report.id}")
            
            # Send the report immediately
            from app.reports.report_scheduler import ReportScheduler
            ReportScheduler.send_report(report)
            
            # Update the last_sent_at timestamp
            report.last_sent_at = datetime.utcnow()
            db.session.commit()
            
            print(f"Test report sent successfully to {admin_user.email}")
            
            # Clean up - delete the test report
            db.session.delete(report)
            db.session.commit()
            print("Test report deleted")
            
            return 0
        except Exception as e:
            print(f"Error testing scheduled reports: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
