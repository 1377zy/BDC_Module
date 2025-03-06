#!/usr/bin/env python
"""
Test script for PDF generation functionality.
This script generates a sample PDF for each report type.
"""
import os
import sys
from datetime import datetime, timedelta
from app import create_app
from app.reports.pdf_generator import (
    generate_inventory_pdf,
    generate_leads_pdf,
    generate_sales_pdf,
    generate_performance_pdf
)

def main():
    """Generate test PDFs for each report type."""
    print(f"[{datetime.now()}] Testing PDF generation functionality...")
    
    # Create the application context
    app = create_app()
    with app.app_context():
        try:
            # Set up date range for reports
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_pdfs')
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate inventory report
            print("Generating inventory report...")
            inventory_pdf = generate_inventory_pdf(start_date, end_date, "Test Inventory Report")
            if inventory_pdf:
                print(f"Inventory PDF generated: {inventory_pdf}")
                # Copy to output directory
                os.system(f'copy "{inventory_pdf}" "{output_dir}\\inventory_report.pdf"')
            
            # Generate leads report
            print("Generating leads report...")
            leads_pdf = generate_leads_pdf(start_date, end_date, "Test Leads Report")
            if leads_pdf:
                print(f"Leads PDF generated: {leads_pdf}")
                # Copy to output directory
                os.system(f'copy "{leads_pdf}" "{output_dir}\\leads_report.pdf"')
            
            # Generate sales report
            print("Generating sales report...")
            sales_pdf = generate_sales_pdf(start_date, end_date, "Test Sales Report")
            if sales_pdf:
                print(f"Sales PDF generated: {sales_pdf}")
                # Copy to output directory
                os.system(f'copy "{sales_pdf}" "{output_dir}\\sales_report.pdf"')
            
            # Generate performance report
            print("Generating performance report...")
            performance_pdf = generate_performance_pdf(start_date, end_date, "Test Performance Report")
            if performance_pdf:
                print(f"Performance PDF generated: {performance_pdf}")
                # Copy to output directory
                os.system(f'copy "{performance_pdf}" "{output_dir}\\performance_report.pdf"')
            
            print(f"All test PDFs generated successfully. Check the {output_dir} directory.")
            return 0
        except Exception as e:
            print(f"Error generating test PDFs: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
