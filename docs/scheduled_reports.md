# Scheduled Reports Documentation

## Overview

The Scheduled Reports feature allows users to automate the generation and delivery of reports via email. This feature is designed to save time and ensure consistent reporting across the dealership.

## Features

- **Automated Generation**: Schedule reports to be generated daily, weekly, or monthly
- **Email Delivery**: Reports are automatically sent to specified recipients
- **PDF Format**: Reports are delivered as professional PDF documents
- **Role-Based Recipients**: Send reports to users based on their roles
- **Customizable Date Ranges**: Configure reports to cover specific time periods
- **Multiple Report Types**: Schedule any of the standard report types

## Report Types

The following report types can be scheduled:

1. **Inventory Reports**: Vehicle status, age distribution, make/model distribution
2. **Lead Reports**: Lead generation statistics, status distribution, source analysis
3. **Sales Reports**: Total sales, revenue metrics, sales by make, daily trends
4. **Staff Performance Reports**: Individual metrics, conversion rates, comparison charts

## User Interface

### Scheduled Reports Page

The Scheduled Reports page allows users to manage their scheduled reports. From this page, users can:

1. View a list of their scheduled reports
2. Create new scheduled reports
3. Edit existing scheduled reports
4. Toggle reports on/off
5. Delete scheduled reports
6. Send reports immediately (on-demand)

### Creating a Scheduled Report

To create a new scheduled report:

1. Navigate to the Reports section
2. Click on "Scheduled Reports"
3. Click the "Create New Report" button
4. Fill in the form with the following information:
   - Report Name: A descriptive name for the report
   - Report Type: Select from Inventory, Leads, Sales, or Performance
   - Frequency: Daily, Weekly, or Monthly
   - Time of Day: When the report should be generated
   - Recipients: Email addresses to receive the report
   - Format: PDF
   - Include Charts: Whether to include visual charts in the report
   - Date Range: The time period the report should cover
   - Report Template: Select a custom template for the report (optional)

### Template Selection

When creating or editing a scheduled report, you can select a custom template to use for the report:

1. Select a report type
2. The system will automatically load templates available for that report type
3. Select a template from the dropdown
4. Click the "Preview" button to see how the report will look with the selected template
5. If no template is selected, the system will use the default template for the report type

For more information about report templates, see the [Report Templates Documentation](report_templates.md).

## Technical Implementation

### Components

The Scheduled Reports feature consists of the following components:

1. **ScheduledReport Model**: Stores report configuration in the database
2. **ReportScheduler**: Utility class for generating and sending reports
3. **PDF Generator**: Generates PDF reports using WeasyPrint
4. **Email Templates**: HTML templates for the email body
5. **PDF Templates**: HTML templates for the PDF reports
6. **CLI Commands**: Flask commands for checking and sending reports
7. **Task Scheduler Integration**: Windows Task Scheduler or cron job integration

### Scheduling

Reports can be scheduled with the following frequencies:

- **Daily**: Reports are sent every day
- **Weekly**: Reports are sent on a specific day of the week
- **Monthly**: Reports are sent on a specific day of the month

### Date Ranges

Reports can cover the following date ranges:

- Last 7 days
- Last 30 days
- This month
- Last month
- This quarter
- This year
- Custom date range

## Setting Up Scheduled Reports

### Email Configuration

To use the Scheduled Reports feature, you must configure the email settings in the `.env` file:

```
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@example.com
```

### Task Scheduler

#### Windows

To set up the Windows Task Scheduler:

1. Run the `setup_scheduled_task.ps1` script as an administrator:
   ```
   powershell -ExecutionPolicy Bypass -File setup_scheduled_task.ps1
   ```

2. This will create a scheduled task that runs daily at 6:00 AM

#### Linux/macOS

To set up a cron job:

1. Run the `setup_cron_job.sh` script:
   ```
   chmod +x setup_cron_job.sh
   ./setup_cron_job.sh
   ```

2. This will create a cron job that runs daily at 6:00 AM

### Manual Checking

You can manually check for scheduled reports using the Flask CLI:

```
flask check-scheduled-reports
```

Or by running the standalone script:

```
python check_scheduled_reports.py
```

## Troubleshooting

### Logs

Scheduled report logs are stored in the `logs/scheduled_reports.log` file. Check this file for any errors or issues with the scheduled reports.

### Common Issues

1. **Reports not being sent**: Check the email configuration in the `.env` file
2. **PDF generation errors**: Ensure WeasyPrint is properly installed
3. **Task scheduler not running**: Check the Windows Task Scheduler or cron job configuration

## Security Considerations

- Email credentials are stored in the `.env` file, which should be kept secure
- Only users with manager or admin roles can create and manage scheduled reports
- Reports are only sent to specified recipients or users with specific roles
