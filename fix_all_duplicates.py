with open('working_app.py', 'r') as file:
    lines = file.readlines()

# Find the first occurrence of update_lead_status_simple
count = 0
for i, line in enumerate(lines):
    if 'def update_lead_status_simple():' in line:
        count += 1
        if count == 1:
            lines[i] = 'def update_lead_status_workflow():\n'
            break

with open('working_app.py', 'w') as file:
    file.writelines(lines)

print("First function renamed back to workflow!")
