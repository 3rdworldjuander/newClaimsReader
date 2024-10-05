import json
import sys
import re
import pandas as pd
from rich import print

def extract_service_authorization(content):
    if pd.isna(content) or content.strip() == "":
        return None
    
    match = re.search(r"Service Authorization \(one SA per page\)#:\s*(\w+)", content)
    if match:
        return match.group(1)
    
    match = re.search(r"Service Authorization.*?(\w+)", content)
    if match:
        return match.group(1)
    
    return None

def cleanup_datofservice_table(date_of_service_table):
 
    results = []

    # Convert cells to a DataFrame
    df = pd.DataFrame(date_of_service_table['cells'])
    
    # Separate header and content rows
    headers = df[df['kind'] == 'columnHeader']
    content = df[df['kind'] == 'content']
    
    # Create a dictionary to map column index to header content
    header_map = dict(zip(headers['column_index'], headers['content']))
    
    # Pivot the content DataFrame
    pivoted = content.pivot(index='row_index', columns='column_index', values='content')
    
    # Rename columns based on header_map
    pivoted.rename(columns=header_map, inplace=True)
    
    # Select only the desired columns
    desired_columns = ["Date of Service", "Start Time", "End Time"]
    result_df = pivoted[desired_columns].reset_index(drop=True)
    

    # print(result_df)
    result_json = result_df.to_dict(orient='records')
    # print(result_json)
    return result_json

def table_pairs_create(data):
    table_pairs = []
    current_pair = {"service_authorization": None, "date_of_service_table": None}
    
    for table in data:
        if 'cells' not in table:
            continue
        
        df = pd.DataFrame(table['cells'])
        table_content = " ".join(df['content'].fillna(''))
        # print(f'this is table_content{table_content}')
        has_date_of_service = ((df['kind'] == 'columnHeader') & 
                               (df['row_index'] == 0) & 
                               df['content'].str.contains("Date of Service")).any()
        
        if "Service Authorization" in table_content:
            sa_number = extract_service_authorization(table_content)
            if current_pair["service_authorization"] is not None:
                table_pairs.append(current_pair)
                current_pair = {"service_authorization": None, "date_of_service_table": None}
            current_pair["service_authorization"] = sa_number
        
        if has_date_of_service:
            current_pair["date_of_service_table"] = cleanup_datofservice_table(table)
            if current_pair["date_of_service_table"] is not None:
                table_pairs.append(current_pair)
                current_pair = {"service_authorization": None, "date_of_service_table": None}

    if current_pair["service_authorization"] is not None or current_pair["date_of_service_table"] is not None:
        table_pairs.append(current_pair)
    
    result = {"table_pairs": table_pairs}
    # print(result)
    return json.dumps(result, indent=2)

def main(json_file_path):
    base_name = json_file_path.split('_')[0].split('/')[1]

    with open(json_file_path, 'r') as file:
        data = json.load(file)

    result = table_pairs_create(data)

    # print(result)

    output_file_path = f"tables/{base_name}_processed_ocr_data.json"
    with open(output_file_path, 'w') as f:
        f.write(result)
    print(f"Processed data has been saved to {output_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json_tables.py <json_file_path>")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    main(json_file_path)