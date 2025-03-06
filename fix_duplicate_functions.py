# Script to fix duplicate function names in working_app.py
import re

def fix_duplicate_functions():
    with open('working_app.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find the second occurrence of the update_lead_status_workflow function
    pattern = r"@app\.route\('/lead/update_status', methods=\['POST'\]\)\s*def update_lead_status_workflow\(\):"
    
    # Replace the second occurrence with update_lead_status_simple
    modified_content = re.sub(pattern, "@app.route('/lead/update_status', methods=['POST'])\ndef update_lead_status_simple():", content, count=1)
    
    with open('working_app.py', 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print("Function renamed successfully!")

if __name__ == "__main__":
    fix_duplicate_functions()
