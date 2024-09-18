from fasthtml import *
from fasthtml.common import *
import os, uvicorn
from starlette.responses import FileResponse
from starlette.datastructures import UploadFile
from claudecleanup import *

app = FastHTML(hdrs=(picolink,))

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

@app.post("/convert")
async def handle_classify(pdf_file:UploadFile):
    
    # Save the uploaded pdf_file
    pdf_file_path = f"uploads/{pdf_file.filename}"
    with open(pdf_file_path, "wb") as f:
        f.write(await pdf_file.read())
    
    # Classify the pdf_file (dummy function for this example)
    result, service_auth = convert(pdf_file_path)
    
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
                Strong(f'Service Authorization No:{service_auth}'),
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