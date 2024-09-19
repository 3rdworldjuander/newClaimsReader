from fasthtml import *
from fasthtml.common import *
import os, uvicorn
from starlette.responses import FileResponse
from starlette.datastructures import UploadFile
from claudecleanup import *
from typing import List

### Experimental Row Render
hdrs = (Style('''
button,input { margin: 0 1rem; }
[role="group"] { border: 1px solid #ccc; }
.edited { outline: 2px solid orange; }
'''), )

app, rt = fast_app(hdrs=hdrs)
### End of Experimental Row Render
# app = FastHTML(hdrs=(picolink,))

# Ensure the uploads directory exists
os.makedirs("uploads", exist_ok=True)
# Ensure the claude directory exists
os.makedirs("claude", exist_ok=True)

# # Your image classification function goes here:
# def convert(pdf_file_path): return f"not hotdog!"

@app.get("/")
def home():
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
    ),
    Br(),
    Div(id="result")
)

### Experimental Row Render
def render_dataframe(df: pd.DataFrame) -> List:
    rows = []
    for _, row in df.iterrows():
        vals = [Td(Input(value=str(v), name=k, oninput="this.classList.add('edited')")) for k, v in row.items()]
        # vals.append(Td(Group(
        #     Button('update', hx_post='update', hx_include="closest tr")
        # )))
        rows.append(Tr(*vals, hx_target='closest tr', hx_swap='outerHTML'))
    return rows

def render_single_value(key, value):
    return Td(Input(value=str(value), name=key, oninput="this.classList.add('edited')"))

### End of Experimantal Row Render


@app.post("/convert")
async def handle_classify(pdf_file:UploadFile):
    
    # Save the uploaded pdf_file
    pdf_file_path = f"uploads/{pdf_file.filename}"
    with open(pdf_file_path, "wb") as f:
        f.write(await pdf_file.read())
    
    # Classify the pdf_file (dummy function for this example)
    result_df, service_auth_df = convert(pdf_file_path)

    ### Experimental Row Render
    result_first_3 = result_df.iloc[:, :3]
    print(result_first_3)
    result_rows = render_dataframe(result_first_3)
    result = Table(Thead(Tr(*[Th(col) for col in result_first_3.columns])), Tbody(*result_rows))

    service_auth = render_single_value('Service Auth', service_auth_df)

    ### End of Experimantal Row Render

    return Div(
        # P(f'Converting {pdf_file.filename}'),
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
                Group(
                    Div(
                        Strong(f'Service Authorization No:'),
                        style="display: flex; align-items: center; justify-content: center;"                        
                        ),
                    Div(service_auth)),
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