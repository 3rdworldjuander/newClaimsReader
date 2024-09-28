import pandas as pd
import sys
import json
import pandas as pd
from rich import print

def cleanup_table_pairs(data):
 
    results = []
    
    for table_pair in data['table_pairs']:
        service_authorization = table_pair['service_authorization']
        date_of_service_table = table_pair['date_of_service_table']
        
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
        
        results.append({
            'service_authorization': service_authorization,
            'date_of_service_table': result_df
        })
    
    # Print or further process the extracted data
    for table_pair in results:
        print(f"Service Authorization: {table_pair['service_authorization']}")
        print("Date of Service Table:")
        print(table_pair['date_of_service_table'].to_string(index=False))
        print()

    return results

def main(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
   
    clean = cleanup_table_pairs(data)
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json_tables.py <json_file_path>")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    main(json_file_path)