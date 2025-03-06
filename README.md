# Auto Dealership BDC Module

## Project Structure
- `app/`: Main application directory
  - `templates/`: HTML templates for the UI
  - `communications/`: Handle communication (e.g., emails, SMS)
  - `appointments/`: Manage appointments for test drives and sales consultations
  - `leads/`: Manage leads and customer interactions
  - `main/`: Main application logic and dashboard
  - `auth/`: User authentication and management
  - `reports/`: Comprehensive reporting and analytics functionality

## Key Features
- Lead management and tracking
- Appointment scheduling and management
- Communication tools (email and SMS)
- Performance analytics and reporting
- User authentication and role management

## Technologies
- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
  - Database: SQLite (can be configured for PostgreSQL)
- Email: SMTP integration
- SMS: Twilio integration
- Data Visualization: Chart.js, Matplotlib, Seaborn
- Data Processing: Pandas

## Initial Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your environment variables
6. Initialize the database: `python init_db.py`
7. Run the application: `python app.py`

## Reporting & Analytics

The BDC Module includes a comprehensive reporting system that provides dealership staff with valuable insights into inventory, leads, sales, and staff performance.

### Available Reports

#### Inventory Reports
- Total vehicles in inventory
- Breakdown by status (Available, On Hold, Sold)
- Age distribution analysis
- Make and model distribution
- Price range distribution
- Export functionality for inventory data

#### Lead Reports
- Lead generation statistics
- Lead status distribution
- Lead source analysis
- Daily lead trend charts
- Conversion rate metrics
- Export functionality for lead data

#### Sales Reports
- Total sales and revenue metrics
- Sales by vehicle make
- Daily sales and revenue trends
- New vs. used sales comparison
- Top-selling models
- Export functionality for sales data

#### Staff Performance Reports
- Individual staff metrics
- Leads assigned and converted
- Appointments scheduled and completed
- Communications sent
- Sales closed
- Conversion rate comparison
- Top performers highlighting

### Scheduled Reports

The BDC Module includes a powerful scheduled reports feature that allows for automated report generation and email delivery.

#### Key Features
- **Automated Generation**: Schedule reports to be generated daily, weekly, or monthly
- **Email Delivery**: Reports are automatically sent to specified recipients
- **PDF Format**: Reports are delivered as professional PDF documents
- **Role-Based Recipients**: Send reports to users based on their roles
- **Customizable Date Ranges**: Configure reports to cover specific time periods
- **Multiple Report Types**: Schedule any of the standard report types

#### Setting Up Scheduled Reports
1. Configure email settings in the `.env` file
2. Set up the task scheduler:
   - Windows: Run `setup_scheduled_task.ps1` as administrator
   - Linux/macOS: Run `setup_cron_job.sh`
3. Create scheduled reports through the UI:
   - Navigate to Reports > Scheduled Reports
   - Click "New Scheduled Report"
   - Fill in the required information
   - Save the report

#### Advanced Features
- **Preview Reports**: Preview reports before scheduling them
- **On-Demand Delivery**: Send scheduled reports immediately
- **Report Archiving**: Automatically archive old reports to save disk space
- **Archive Management**: Download archived reports when needed

For more detailed information, see the [Scheduled Reports Documentation](docs/scheduled_reports.md).

### Report Features

- **Date Range Filtering**: All reports can be filtered by custom date ranges
- **Visual Analytics**: Interactive charts and graphs for data visualization
- **Tabular Data**: Detailed tables with sortable columns
- **Export Options**: CSV export for further analysis in spreadsheet software
- **Print-Friendly Versions**: Optimized layouts for printing reports
- **Scheduled Reports**: Automated report generation and email delivery
- **Custom Templates**: Create and use custom report templates for consistent branding

### Report Templates

The BDC Module includes a powerful template management system that allows users to create, edit, and use custom report templates.

#### Key Features
- **Template Creation**: Create custom templates with branded headers, footers, and content sections
- **Template Preview**: Preview templates with sample data before using them
- **Template Selection**: Select templates when creating or editing scheduled reports
- **Report Type Filtering**: Templates are categorized by report type for easy selection
- **Default Templates**: Set default templates for each report type
- **PDF Generation**: Reports are generated using the selected template's styling and layout

#### Using Report Templates
1. **Creating Templates**:
   - Navigate to Reports > Report Templates
   - Click "New Template"
   - Select a report type
   - Customize header, content, and footer sections
   - Save the template

2. **Previewing Templates**:
   - From the templates list, click the "Preview" button
   - View how the template will look with sample data
   - Make adjustments as needed

3. **Using Templates in Scheduled Reports**:
   - When creating or editing a scheduled report, select a template from the dropdown
   - Click the "Preview" button to see how the report will look with the selected template
   - Save the scheduled report to use the template for future reports

### Accessing Reports

Reports can be accessed through:
1. The main navigation bar's "Reports" dropdown menu
2. The dashboard's "Reports & Analytics" section
3. Direct links from relevant sections (e.g., Leads, Inventory)

### Exporting Data
- Inventory data can be exported as a CSV file
- Lead data can be exported as a CSV file
- Sales data can be exported as a CSV file
- Staff performance data can be exported as a CSV file
