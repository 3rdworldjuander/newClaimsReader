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
    return Title("Service Log Converter"), Main(
        H1("FastHTML based Service Log Converter"),
        Form(
            Input(type="file", name="pdf_file", accept=".pdf", required=True),
            Button("Convert"),
            enctype="multipart/form-data",
            hx_post="/convert",
            hx_target="#result"
        ),
        Br(), Div(id="result"),
        cls="container"
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
        P(f"Conversion result: {result}, Service Auth no: {service_auth}"),
        Img(src=f"/uploads/{pdf_file.filename}", alt="Uploaded pdf_file", style="max-width: 300px;; transform: rotate(-90deg);")
    )

@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    return FileResponse(f"uploads/{filename}")

if __name__ == '__main__': uvicorn.run("main:app", host='127.0.0.1', port=int(os.getenv("PORT", default=5000)), reload=True)