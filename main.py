import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

from backend.database import database, metadata, engine
from backend.models import pdfs, tables  # SQLAlchemy table definitions

import shutil
import tabula  # Used to extract tables from PDF
import os
import uuid
import json


# Lifespan function handles startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()       # On startup
    metadata.create_all(engine)    # Create tables if not exist
    yield
    await database.disconnect()    # On shutdown
    
    
# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)


# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for in-memory fruit API
class Fruit(BaseModel):
    name: str

class Fruits(BaseModel):
    fruits: List[Fruit]







# In-memory fruit store
memory_db = {"fruits": []}

@app.get("/fruits", response_model=Fruits)
def get_fruits():
    return Fruits(fruits=memory_db["fruits"])

@app.post("/fruits", response_model=Fruit)
def add_fruit(fruit: Fruit):
    memory_db["fruits"].append(fruit)
    return fruit

# Folder to store uploaded PDFs
UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, save it locally, extract tables using Tabula,
    and store both metadata and extracted table data in the database.
    """
    try:
        # Step 1: Save PDF locally
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Step 2: Save metadata into the 'pdfs' table
        query = pdfs.insert().values(filename=filename)
        pdf_id = await database.execute(query)

        # Step 3: Extract tables using Tabula
        dfs = tabula.read_pdf(filepath, pages="all", multiple_tables=True)

        if not dfs:
            print("No tables extracted from PDF.")

        # Step 4: Save extracted tables to DB
        for i, df in enumerate(dfs):
            table_data = df.to_json(orient="split")
            await database.execute(tables.insert().values(
                pdf_id=pdf_id,
                page_number=i + 1,
                table_data=table_data
            ))

        print("Returning PDF ID:", pdf_id)
        return {"message": "PDF uploaded and processed", "pdf_id": pdf_id}

    except Exception as e:
        print("Error during upload:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/tables/{pdf_id}")
async def get_tables(pdf_id: int):
    query = tables.select().where(tables.c.pdf_id == pdf_id)
    results = await database.fetch_all(query)
    
    # Convert JSON strings to Python dicts before returning
    table_list = []
    for row in results:
        table_dict = dict(row)
        table_dict["table_data"] = json.loads(table_dict["table_data"])  # or json.loads(...)
        table_list.append(table_dict)
    
    return JSONResponse(content=table_list)

# Uvicorn entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
