with open('working_app.py', 'r') as file:
    lines = file.readlines()

for i, line in enumerate(lines):
    if 'def update_lead_status_workflow():' in line:
        print(f"Found at line {i+1}: {line.strip()}")
        print(f"Previous line: {lines[i-1].strip()}")
        print("---")
