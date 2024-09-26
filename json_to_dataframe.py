import json
import pandas as pd
import sys
import csv

json_file_path = sys.argv[1]
base_name = json_file_path.split('_')[1]

# Load the JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Function to extract table data
# def extract_table(table_data):
#     rows = []
#     max_columns = 0
    
#     for cell in table_data['cells']:
#         row_index = cell['row_index']
#         column_index = cell['column_index']
#         content = cell['content']
#         print(row_index, column_index, content)
        
#         # Update max_columns
#         max_columns = max(max_columns, column_index + 1)
        
#         # Check if it's a header cell
#         # if row_index == 0:
#         #     headers.append(content)
#         # else:
#         while len(rows) <= row_index:
#             rows.append({})
        
#         rows[row_index][column_index] = content
    
#     # Ensure all rows have the same number of columns
#     for row in rows:
#         for i in range(max_columns):
#             if i not in row:
#                 row[i] = ''
    
#     # Create DataFrame
#     df = pd.DataFrame(rows)
#     df.columns = [f'Column {i+1}' for i in range(max_columns)]
#     return df

# Extract tables
tables = data['tables']

tables_json = {"tables": tables}

# Save the JSON to a local file
output_json_path = f"justTables_{base_name}.json"
with open(output_json_path, "w") as output_file:
    json.dump(tables_json, output_file, indent=4)
print("Analysis result saved to:", output_json_path)


# # Dictionary to store DataFrames
# table_df = {}

# # Process each table
# for i, table in enumerate(tables):
#     df = extract_table(table)
#     table_name = f"table_{i+1}"
#     table_df[table_name] = df
#     print(f"Created Dataframe: {table_name}")
#     print(df.shape)
#     print("\n")
#     output_csv_path = f"{base_name}_{table_name}.csv"
#     table_df[table_name].to_csv(output_csv_path, index=False)

# You can now use the dataframes for further processing or analysis