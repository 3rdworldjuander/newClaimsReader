import json
import sys
from rich import print

def process_azure_ocr_json(data):
    table_pairs = []
    current_pair = {"service_authorization": None, "date_of_service_table": None}
    
    for table in data:
        print(f'table{table}')  # troubleshooting
        table_content = ""
        has_date_of_service = False
        
        if 'cells' in table:
            for cell in table['cells']:
                cell_content = cell.get('content', '')
                table_content += cell_content + " "
                
                # Check for "Date of Service" in header
                if cell.get('kind') == 'columnHeader' and cell.get('row_index') == 0 and "Date of Service" in cell_content:
                    has_date_of_service = True
        
        # Check for "Service Authorization"
        if "Service Authorization" in table_content:
            # If we already have a service authorization in the current pair, start a new pair
            if current_pair["service_authorization"] is not None:
                table_pairs.append(current_pair)
                current_pair = {"service_authorization": None, "date_of_service_table": None}
            current_pair["service_authorization"] = table_content.strip()
        
        # Store the table if it has "Date of Service" header
        if has_date_of_service:
            current_pair["date_of_service_table"] = table
            
            # If we have both parts of the pair, add it to the list and start a new pair
            if current_pair["service_authorization"] is not None:
                table_pairs.append(current_pair)
                current_pair = {"service_authorization": None, "date_of_service_table": None}
    
    # Add the last pair if it's not empty
    if current_pair["service_authorization"] is not None or current_pair["date_of_service_table"] is not None:
        table_pairs.append(current_pair)
    
    # Prepare the result
    result = {
        "table_pairs": table_pairs
    }
    
    return json.dumps(result, indent=2)

# Get the JSON file path from command line argument
json_file_path = sys.argv[1]
base_name = json_file_path.split('_')[0].split('/')[1]

# Load the JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Process the data
result = process_azure_ocr_json(data)

# Print the result
print(result)

# Save the result to a file
output_file_path = f"tables/{base_name}_processed_ocr_data.json"
with open(output_file_path, 'w') as f:
    f.write(result)
print(f"Processed data has been saved to {output_file_path}")