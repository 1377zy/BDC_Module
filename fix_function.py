with open('working_app.py', 'r') as file:
    lines = file.readlines()

# Find the second occurrence of update_lead_status_workflow
count = 0
for i, line in enumerate(lines):
    if 'def update_lead_status_workflow():' in line:
        count += 1
        if count == 2:
            lines[i] = 'def update_lead_status_simple():\n'
            break

with open('working_app.py', 'w') as file:
    file.writelines(lines)

print("Function renamed successfully!")
