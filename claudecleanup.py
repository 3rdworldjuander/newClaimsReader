# claude_cleanup.py
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import anthropic
import os
import sys
import io
import pandas as pd
from dotenv import load_dotenv
from rich import print
import json
from json_tables import *
from clean_tables import *

# Configuration
config = {
    'UPLOAD_FOLDER': 'uploads/',
    'ALLOWED_EXTENSIONS': {'pdf'},
    'PROCESSED_FOLDER': 'processed/',
    'CSV_OCR_NAME': '_ocr',
    'CSV_OCR_DIR': 'ocr/',
    'CSV_CLAUDE_NAME': '_claude',
    'CSV_CLAUDE_DIR': 'claude/',
    'HEADER_TEXT': 'Date of Service'
}

def load_env_variables():
    """Load environment variables from .env file."""
    load_dotenv()
    azu_endpoint = os.environ.get("AZURE_DOCINT_URL")
    azu_key = os.environ.get("AZURE_DOCINT_KEY")
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    prompt = os.environ.get("prompt")                       # Placeholder for when I want to hide my prompt
    if not claude_api_key or not azu_endpoint or not azu_key:
        raise ValueError("CLAUDE_API_KEY, AZURE_DOCINT_URL and AZURE_DOCINT_KEY must be set in the environment variables.")
    return azu_endpoint, azu_key, claude_api_key, prompt

def init_claude_client(api_key):
    """Initialize the OpenAI client with the API key."""
    return anthropic.Anthropic(api_key=api_key)

def get_claude_response(client, json):
    """Get the corrected table content from OpenAI."""
    prompt = (f'You are a data analyst. You will be provided with a json file. Within the json file is an array called date_of_service_table '
            f'There could me multiple date_of_service arrays in the json file. '
            f'The objects within the array have pairs of key value content. The data is captured via OCR which means that there could be '
            f'mistakes in how the OCR converts the handwritten text. Correct the data as follows '
            f'for the key "Date of Service" the value should be a date in MM/DD/YYYY format, make necessary corrections if the format is incorrect '
            f'for the key "Start Time" the value should be time in 12-hour time format, make necessary corrections if the format is incorrect '
            f'for the key "End Time" the value should be time in 12-hour time format, make necessary corrections if the format is incorrect '
            f'Check the other rows to infer what dates and times should be written based on what was detected and the data in the other rows. '
            f'make the correction in the "content": portion of the json and keep the structure of the original json file.'
            f'Just reply with the corrected json and nothing else.'
            f'Here is the json: {json}')

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(f'Response is type....{type(response)}')
    print(f'Actual response is....{response}')
    print(f'This is the response content....{response.content}')
    return response.content

def analyze_document(document_analysis_client, file_path, model_id):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document(
        model_id
        , document=f
        )
    return poller.result()

### Useful tools ###
def save_json_to_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
### End of Useful tools ###

def convert(pdf_file_path):
    azu_endpoint, azu_key, claude_api_key, claude_prompt = load_env_variables()
    model_id = "prebuilt-layout"
    document_analysis_client = DocumentAnalysisClient(endpoint=azu_endpoint, credential=AzureKeyCredential(azu_key))

    # Extract the original filename for reference
    # find a better way to handle this without relying on '/' split
    base_name = pdf_file_path.split('/')[1].split('.')[0]

    ### ANALYSIS STARTS HERE ###

    # Analyze doc with Azure DocInt
    result = analyze_document(document_analysis_client, pdf_file_path, model_id)
    result_json = result.to_dict()

    # save_json_to_file(result_json, f"json/{base_name}full_result.json")     # Troubleshooting tools

    # Extract tables
    tables = result_json['tables']

    # save_json_to_file(tables, f"json/{base_name}tables.json")       # Troubleshooting tools

    # create table pairs of service auth + service dates
    tables_json = table_pairs_create(tables)    

    # # Current working implementation 27-Sep
    # tables_json = {"tables": tables}
    # print(tables_json)
    # # END Current working implementation 27-Sep

    ## Start of Claude Cleanup ##

    # Setting up Claude
    client = init_claude_client(claude_api_key)
    response_content = get_claude_response(client, tables_json)
    what_is_this = response_content[0].text.strip()
    print(type(what_is_this))
    print(what_is_this)

    # Save the CSV data to a file

    output_file = os.path.join(config['CSV_CLAUDE_DIR'],f'{base_name}_claude_output.json')
    with open(output_file, 'w') as file:
        file.write(what_is_this)
        
    print(f"JSON data has been saved to {output_file}")

    # df = pd.read_csv(io.StringIO(what_is_this))
    # service_auth = df['Service Auth'].unique()
    # service_auth_str = str(int(service_auth))
    # print(type(service_auth_str))
    # print(f'Service Authorization No: {service_auth_str}')

    ## End of Claude Cleanup ##

    ## ANALYSIS ENDS HERE ###

    # ### DUMMY DATA FOR TESTING ###

    # csv_file_path = "claude/20240916120327_001_claude_output.csv"

    # df = pd.read_csv(csv_file_path)
    # service_auth_str = df['Service Auth'].unique()[0]

    # # with open(csv_file_path, 'r') as file:
    # #     df = file.read()
    # # service_auth_str = '12510932'

    # ### END OF DUMMY DATA FOR TESTING ###

    # print(df)
    # print(service_auth_str)

    # return df, service_auth_str
    return what_is_this

if __name__ == "__main__":
    pdf_file_path = sys.argv[1]
    convert(pdf_file_path)
