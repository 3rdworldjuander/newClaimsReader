from fasthtml import *
from fasthtml.common import *
import os, uvicorn
from starlette.responses import FileResponse
from starlette.datastructures import UploadFile
from claudecleanup import *
from typing import List
from uuid import uuid4

### DB experiment ###
db = database('sqlite.db')
### End DB Experiment

### Experimental Row Render
hdrs = (Style('''
button,input { margin: 0 1rem; }
[role="group"] { border: 1px solid #ccc; }
.edited { outline: 2px solid orange; }
'''), )

app, rt = fast_app(hdrs=hdrs)
### End of Experimental Row Render

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
        P("This web application extracts data from the claims form for use in NYEIS/EI-Hub claims processing."),

    Group(
        Input(type="file", name="pdf_file", accept=".pdf", required=True),
        Button("Convert", 
               hx_post="/convert",
               hx_target="#result",
               hx_encoding="multipart/form-data",
               hx_include='previous input'),
        ### DB experiment ###
        A('Download', href='download', type="button")
        ### End DB Experiment
    ),
    Div(id='progress_bar'),
    Div(id="result")
)

### Experimental Row Render
def render_row(row):
    vals = [Td(Input(value=v, name=k, 
                     oninput="this.classList.add('edited')",
                     style = "font-size: 0.8em; padding: 2px; margin: 0; width: 95%;",),
                     style = "padding: 2px;") for k,v in row.items()]
    vals.append(Td(Group(
                   Button('update', hx_post='update', hx_include="closest tr",
                          style="font-size: 0.8em; padding: 2px;")),
                          style = "padding: 2px;"))
    return Tr(*vals, hx_target='closest tr', hx_swap='outerHTML', style="line-height: 1;")

def render_dataframe(df: pd.DataFrame) -> List:
    rows = []
    for _, row in df.iterrows():
        vals = [Td(Input(value=str(v), name=k, 
                         oninput="this.classList.add('edited')",
                         style = "font-size: 0.8em; padding: 2px; margin: 0; width: 95%;",),
                         style = "padding: 2px;") for k, v in row.items()]
        vals.append(Td(
            Button('update', hx_post='update', hx_include="closest tr",
                   style="font-size: 0.8em; padding: 2px;")),
                   style="font-size: 0.8em; padding: 2px;")
        rows.append(Tr(*vals, hx_target='closest tr', hx_swap='outerHTML', style="line-height: 1;"))
    return rows

def render_single_value(key, value):
    return Td(Input(value=str(value), name=key, oninput="this.classList.add('edited')"))
### End of Experimantal Row Render

### DB experiment ###
@rt
def download(sess):
    tbl = db[sess['id']]
    csv_data = [",".join(map(str, tbl.columns_dict))]
    csv_data += [",".join(map(str, row.values())) for row in tbl()]
    headers = {'Content-Disposition': 'attachment; filename="data.csv"'}
    return Response("\n".join(csv_data), media_type="text/csv", headers=headers)

@rt('/update')
def post(d:dict, sess): return render_row(db[sess['id']].update(d))


### End DB Experiment


@app.post("/convert")
async def handle_classify(pdf_file:UploadFile, sess): 
    # Save the uploaded pdf_file
    pdf_file_path = f"uploads/{pdf_file.filename}"
    with open(pdf_file_path, "wb") as f:
        f.write(await pdf_file.read())
    
    # Classify the pdf_file (dummy function for this example)
    result_df, service_auth_df = convert(pdf_file_path)

    db[sess['id']].drop(ignore=True)
    for _, row in result_df.iterrows():
        row_dict = row.to_dict()
        print(row_dict)
        db[sess['id']].insert(row_dict, pk='id')
        # db[sess['id']](**row_dict)   

    header = Tr(*map(Th, db[sess['id']].columns_dict))
    vals = [render_row(row) for row in db[sess['id']]()]
    result =  Table(Thead(header), Tbody(*vals))

    # ### Experimental Row Render
    # result_first_3 = result_df.iloc[:, :3]
    # print(result_first_3)
    # result_rows = render_dataframe(result_first_3)
    # result = Table(Thead(Tr(*[Th(col) for col in result_first_3.columns])), Tbody(*result_rows))

    service_auth = render_single_value('Service Auth', service_auth_df)
    # ### End of Experimantal Row Render

    return Div(
        Div(
            Div(
                Strong(f'Converting {pdf_file.filename}'),
                Div(
                    Embed(
                        src=f"/uploads/{pdf_file.filename}", 
                        type='application/pdf',
                        # style="width: 150%; height: 150%;  scale(0.66); transform-origin: top center;"  ### THIS WORKS
                        style="width: 100%; height: 100%; padding-bottom: 75%; transform: rotate(-90deg); transform-origin: center ;"   ### THIS IS ALMOST PERFECT
                    ),
                    # style="width: 100%; aspect-ratio: 1/1.4; display: flex; justify-content: center; align-items: center; overflow: hidden;"  ### THIS WORKS
                    style="width: 100%; display: flex; overflow: hidden;"   ### THIS IS PERFECT
                ),
                style="display: flex; flex-direction: column; align-items: center;"
                # style="display: flex; flex-direction: column; align-items: center; height: 100%;"
            ),
            Div(
                # Group(
                #     Div(
                #         Strong(f'Service Authorization No:'),
                #         style="display: flex; align-items: center; justify-content: center;"                        
                #         ),
                #     Div(service_auth)),
                Div(result),
                style="overflow: auto;"
            ),
            style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; width: 100%; height: 100vh;"
            )
        )


@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    return FileResponse(f"uploads/{filename}")

if __name__ == '__main__': uvicorn.run("main:app", host='127.0.0.1', port=int(os.getenv("PORT", default=5000)), reload=True)