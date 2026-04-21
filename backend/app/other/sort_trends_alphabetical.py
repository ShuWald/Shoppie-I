import csv
import os

# Get the parent directory (backend/app)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_file = os.path.join(parent_dir, "trends_data.csv")
output_file = os.path.join(parent_dir, "trends_data_alphabetical.csv")

# Read CSV and sort by keyword
rows = []
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Sort alphabetically by keyword column
rows.sort(key=lambda x: x['keyword'].lower())

# Write sorted data to new CSV
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    if rows:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

print(f"✓ Sorted {len(rows)} products alphabetically by keyword")
print(f"✓ Saved to: {output_file}")
