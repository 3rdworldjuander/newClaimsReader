from fasthtml import *
from fasthtml.common import *
import os, uvicorn
from starlette.responses import FileResponse
from starlette.datastructures import UploadFile
from claudecleanup import *
from dict_to_db import *
from typing import List
from uuid import uuid4
import json

hdrs = (Style('''
button,input { margin: 0 1rem; }
[role="group"] { border: 1px solid #ccc; }
.edited { outline: 2px solid orange; }
'''), Script('''
function collectTableData() {
    let tablePairs = [];
    document.querySelectorAll('.table-pair').forEach(pairDiv => {
        let serviceAuth = pairDiv.querySelector('input[name="service_authorization"]').value;
        let tableRows = pairDiv.querySelectorAll('table tbody tr');
        let tableData = Array.from(tableRows).map(row => {
            let inputs = row.querySelectorAll('input');
            return {
                "Date of Service": inputs[0].value,
                "Start Time": inputs[1].value,
                "End Time": inputs[2].value
            };
        });
        tablePairs.push({
            service_authorization: serviceAuth,
            date_of_service_table: tableData
        });
    });
    document.getElementById('table-data').value = JSON.stringify({table_pairs: tablePairs});
}
             
function showProgressMessage() {
    document.getElementById('progress_bar').innerHTML = "Converting... Please wait";
}

'''))

app, rt = fast_app(hdrs=hdrs)

# Ensure the uploads directory exists
os.makedirs("uploads", exist_ok=True)
# Ensure the claude directory exists
os.makedirs("claude", exist_ok=True)

@app.get("/")
def homepage(sess):
    if 'id' not in sess: sess['id'] = str(uuid4())
    print(f'Session ID is{sess}')
    return Title("Service Log Converter"), Titled(
        H1("FastHTML based Service Log Converter"),
        P("This web application extracts data from the claims form for use in NYEIS/EI-Hub claims processing (mm/dd/yyyy)."),
    Group(
        Input(type="file", name="pdf_file", accept=".pdf", required=True),
        Button("Convert", 
               hx_post="/convert",
               hx_target="#progress_bar, #result",
               hx_encoding="multipart/form-data",
               hx_include='previous input',
               onclick="showProgressMessage()"),
    ),
    Div(id="progress_bar"),
    Div(id="result")
)

def render_table(table_data):
    headers = table_data[0].keys()
    rows = []
    for row in table_data:
        vals = [Td(Input(value=str(row[k]), name=k, 
                         oninput="this.classList.add('edited')",
                         style="font-size: 0.8em; padding: 2px; margin: 0; width: 95%;"),
                   style="padding: 2px;") for k in headers]
        rows.append(Tr(*vals, hx_target='closest tr', hx_swap='outerHTML', style="line-height: 1;"))
    return Table(
        Thead(Tr(*[Th(header) for header in headers])),
        Tbody(*rows),
        style="width: 100%; border-collapse: collapse;"
    )

@rt('/queue')
def post(d:dict, sess):
    print('Queue Button hit')
    print(sess)
    table_data = json.loads(d.get('table_data', '{}'))
    db_result = import_service_data(table_data)
    print(db_result)

    # for pair in table_data['table_pairs']:
    #     preview_sa = pair['service_authorization']
    #     preview_table = pair['date_of_service_table']

    #     print(f'this is Service Auth {preview_sa}')
    #     # print(preview_table)
    #     for row in preview_table:
    #         print(row['Date of Service'])
    #         print(row['Start Time'])
    #         print(row['End Time'])

    # output_file = f'todb/{sess}.json'
    # with open(output_file, 'w') as file:
    #     file.write(table_data)
        
    # with open(output_file, 'w') as fp:
    #     json.dump(table_data, fp)

    # print(f"JSON data has been saved to {output_file}")

    return "Data queued successfully!", db_result

@app.post("/convert")
async def handle_classify(pdf_file:UploadFile, sess): 
    # Save the uploaded pdf_file
    pdf_file_path = f"uploads/{pdf_file.filename}"
    with open(pdf_file_path, "wb") as f:
        f.write(await pdf_file.read())
    
    # Convert the pdf_file
    result_json = convert(pdf_file_path)
    result_data = json.loads(result_json)

    tables_html = []
    for pair in result_data['table_pairs']:
        service_auth = pair['service_authorization']
        table_data = pair['date_of_service_table']
        
        tables_html.append(
            Div(
                Group(
                    Div(
                        Strong('Service Authorization No:'),
                        style="display: flex; align-items: center; justify-content: center;"
                    ),
                    Div(Input(value=str(service_auth), name='service_authorization', 
                              oninput="this.classList.add('edited')", 
                              style="font-size: 0.8em; padding: 2px; margin: 0;"),
                        id=f"service-auth-{service_auth}"),
                    style="overflow: auto; margin-bottom: 10px;"
                ),
                render_table(table_data),
                style="margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;",
                cls="table-pair"
            )
        )

    response = Div(
        Div(
            Div(*tables_html, style="overflow: auto;"),
            Div(
                Strong(f'Done converting {pdf_file.filename}'),
                Div(
                    Embed(
                        src=f"/uploads/{pdf_file.filename}",
                        type='application/pdf',
                        style="width: 100%; height: 100%; padding-bottom: 75%; transform: rotate(-90deg); transform-origin: center ;"
                    ),
                    style="width: 100%; display: flex; overflow: hidden;"
                ),
                style="display: flex; flex-direction: column; align-items: center;"
            ),
            style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; width: 100%; height: calc(100vh - 50px);"
        ),
        Div(
            Input(type="hidden", id="table-data", name="table_data"),
            Button('Queue', hx_target="#queue_result", hx_post='queue', hx_include="#table-data", onclick="collectTableData()"),
            style="display: flex; justify-content: center; align-items: center; height: 50px;"
        ),
        Div(id="queue_result"),
        style="display: flex; flex-direction: column; height: 100vh;"
    )

    prog_update = Div()

    return response, prog_update

@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    return FileResponse(f"uploads/{filename}")

if __name__ == '__main__': uvicorn.run("main:app", host='127.0.0.1', port=int(os.getenv("PORT", default=5000)), reload=True)
