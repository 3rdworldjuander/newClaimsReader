# claude_cleanup.py
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import anthropic
import os
import sys
import io
import pandas as pd
from dotenv import load_dotenv

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
    if not claude_api_key or not azu_endpoint or not azu_key:
        raise ValueError("CLAUDE_API_KEY, AZURE_DOCINT_URL and AZURE_DOCINT_KEY must be set in the environment variables.")
    return azu_endpoint, azu_key, claude_api_key

def init_claude_client(api_key):
    """Initialize the OpenAI client with the API key."""
    return anthropic.Anthropic(api_key=api_key)

def get_claude_response(client, json):
    """Get the corrected table content from OpenAI."""
    prompt = (f'You are a data analyst. You will be provided with a json file. The Json file has a table with column identifiers as "Date of Service", "Start Time", "End Time" '
              f'the first column is a date column with dates in the MM/DD/YYYY format and the other two columns '
              f'are time in 12-hour formats. The data is captured via OCR which means that there could be '
              f'mistakes in how the OCR converts the handwritten text. Correct the data in the first column and make '
              f'sure that the resulting date follows the MM/DD/YYYY format. If there are errors in '
              f'the second and third column, correct them by making sure that they follow the 12-hour time format. '
              f'Check the other rows to infer what dates and times should be written based on what was detected and the data in the other rows. '
              f'if there are any cells in the second or third column with nan, remove the whole row.  '
              f'please return a csv table with just the columns "Service Date", "Start Time", "End Time". Create a fourth column with header "Service Auth" and enter the Service Authorization number in all the rows.'
              f'Just reply with the corrected csv table and nothing else.'
              f'Here is the table of service dates and times: {json}')

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
        # , content_type="application/json"
        )
    return poller.result()

def convert(pdf_file_path):
    azu_endpoint, azu_key, claude_api_key = load_env_variables()
    model_id = "prebuilt-layout"
    document_analysis_client = DocumentAnalysisClient(endpoint=azu_endpoint, credential=AzureKeyCredential(azu_key))

    # Extract the original filename for reference
    # find a better way to handle this without relying on '/' split
    base_name = pdf_file_path.split('/')[1].split('.')[0]

    # Analyze doc with Azure DocInt
    result = analyze_document(document_analysis_client, pdf_file_path, model_id)
    result_json = result.to_dict()

    # Extract tables
    tables = result_json['tables']

    tables_json = {"tables": tables}
    print(tables_json)

    # Setting up Claude
    client = init_claude_client(claude_api_key)
    response_content = get_claude_response(client, tables_json)
    what_is_this = response_content[0].text.strip()
    print(type(what_is_this))
    print(what_is_this)

    # Save the CSV data to a file

    output_file = os.path.join(config['CSV_CLAUDE_DIR'],f'{base_name}_claude_output.csv')
    with open(output_file, 'w') as file:
        file.write(what_is_this)
        
    print(f"CSV data has been saved to {output_file}")

    df = pd.read_csv(io.StringIO(what_is_this))
    service_auth = df['Service Auth'].unique()
    service_auth_str = str(int(service_auth))
    print(type(service_auth_str))
    print(f'Service Authorization No: {service_auth_str}')

    return df, service_auth_str

if __name__ == "__main__":
    pdf_file_path = sys.argv[1]
    convert(pdf_file_path)
