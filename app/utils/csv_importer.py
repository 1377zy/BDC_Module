import csv
import os
from datetime import datetime
from flask import current_app, flash

def validate_csv_headers(headers, required_headers):
    """Validate that the CSV file contains all required headers"""
    missing_headers = [h for h in required_headers if h not in headers]
    if missing_headers:
        return False, f"Missing required headers: {', '.join(missing_headers)}"
    return True, "Headers validated successfully"

def import_leads_from_csv(file_path):
    """Import leads from a CSV file"""
    leads = []
    required_headers = ['first_name', 'last_name', 'email', 'phone', 'status', 'vehicle_interest']
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)
            
            # Validate headers
            headers = reader.fieldnames
            valid, message = validate_csv_headers(headers, required_headers)
            if not valid:
                return False, message
            
            # Process rows
            for row in reader:
                # Clean and validate data
                lead = {
                    'first_name': row.get('first_name', '').strip(),
                    'last_name': row.get('last_name', '').strip(),
                    'email': row.get('email', '').strip().lower(),
                    'phone': row.get('phone', '').strip(),
                    'status': row.get('status', 'New').strip(),
                    'vehicle_interest': row.get('vehicle_interest', '').strip(),
                    'created_at': datetime.now()
                }
                
                # Add optional fields if present
                if 'notes' in row:
                    lead['notes'] = row.get('notes', '').strip()
                
                leads.append(lead)
                
        return True, leads
    except Exception as e:
        return False, f"Error importing CSV: {str(e)}"

def get_next_lead_id(existing_leads):
    """Get the next available lead ID"""
    if not existing_leads:
        return 1
    return max(lead['id'] for lead in existing_leads) + 1

def import_leads(file_path, existing_leads):
    """Import leads and assign IDs"""
    success, result = import_leads_from_csv(file_path)
    
    if not success:
        return False, result
    
    next_id = get_next_lead_id(existing_leads)
    
    # Assign IDs to new leads
    for i, lead in enumerate(result):
        lead['id'] = next_id + i
    
    return True, result
