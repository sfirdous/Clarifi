import uvicorn
from fastapi import FastAPI, File, UploadFile,HTTPException,APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

from backend.database import database, metadata, engine
from backend.models import pdfs, tables  # SQLAlchemy table definitions

from sqlalchemy import Table, MetaData, select

import shutil
import tabula  # Used to extract tables from PDF
import os
import uuid
import json
import pandas as pd


# Lifespan function handles startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()       # On startup
    metadata.create_all(engine)    # Create tables if not exist
    yield
    await database.disconnect()    # On shutdown
    
    
# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)

router = APIRouter()
metadata = MetaData()
metadata.reflect(bind=engine)

app.include_router(router)


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

UPLOAD_DIR = "uploaded_pdfs"
TABLES_DIR = "extracted_tables"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)


@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{pdf_id}.pdf")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"Saved PDF to {file_path}")

        # ---------------- TABLE EXTRACTION ----------------
        try:
            tables = tabula.read_pdf(
                file_path,
                pages='all',
                multiple_tables=True,
                guess=False,
                lattice=True  # You can also test with stream=True
            )
        except Exception as e:
            print("Tabula extraction failed:", e)
            raise HTTPException(status_code=500, detail=f"Table extraction error: {str(e)}")

        if not tables:
            raise HTTPException(status_code=400, detail="No tables found in PDF")

        all_rows = []
        for page_num, df in enumerate(tables, start=1):
            df.fillna("", inplace=True)
            for _, row in df.iterrows():
                row_dict = {f"col_{i+1}": str(val) for i, val in enumerate(row)}
                row_dict["page_number"] = page_num
                all_rows.append(row_dict)

        # Save to CSV (optional but good for debugging)
        df_combined = pd.DataFrame(all_rows)
        df_combined.to_csv(os.path.join(TABLES_DIR, f"{pdf_id}.csv"), index=False)

        return {"pdf_id": pdf_id}

    except Exception as e:
        print("PDF processing failed:", e)
        raise HTTPException(status_code=500, detail="Failed to process PDF")


@app.get("/tables/{pdf_id}")
def get_tables(pdf_id: str):
    try:
        table_path = os.path.join("extracted_tables", f"{pdf_id}.csv")
        print("Looking for:", table_path)

        if not os.path.exists(table_path):
            return JSONResponse(status_code=404, content={"error": "Table file not found"})

        df = pd.read_csv(table_path)

        if df.empty:
            return JSONResponse(status_code=204, content={"error": "No table data found"})

        # Replace problematic float values
        df.replace([float('inf'), float('-inf')], None, inplace=True)
        df.fillna("", inplace=True)

        result = df.to_dict(orient="records")
        return result
    except Exception as e:
        print("Error loading table:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})



import numpy as np 

def merge_nan_rows(df, nan_threshold=0.5):
    """
    Replaces NaNs with empty strings and merges rows with a high
    percentage of empty values into the row above.
    """
    df = df.fillna('')  # Replace NaN with empty strings
    df = df.reset_index(drop=True)

    # Calculate how many empty strings (used to be NaNs) per row
    empty_counts = (df == '').sum(axis=1) / df.shape[1]
    rows_to_merge = empty_counts > nan_threshold

    for i in range(1, len(df)):
        if rows_to_merge[i]:
            df.iloc[i - 1] = df.iloc[i - 1].astype(str).str.cat(df.iloc[i].astype(str), sep=' ')
            df.iloc[i] = ''  # Mark for removal

    # Drop rows where all cells are empty
    df = df[~(df == '').all(axis=1)].reset_index(drop=True)
    return df


def detect_description_column(columns: list[str], sample_rows: list[dict]) -> str | None:
    # Priority 1: Based on common keywords
    keywords = ['description', 'details', 'info', 'narration', 'particulars']
    for col in columns:
        if any(kw in col.lower() for kw in keywords):
            return col

    # Priority 2: Based on longest average string length (text-heavy column)
    avg_lengths = {}
    for col in columns:
        lengths = [len(str(row.get(col, ""))) for row in sample_rows if row.get(col)]
        if lengths:
            avg_lengths[col] = sum(lengths) / len(lengths)

    if avg_lengths:
        return max(avg_lengths, key=avg_lengths.get)

    return None



@router.get("/tables/{table_id}/description-column")
async def get_description_column(table_id: str):
    try:
        table_name = f"table_{table_id.replace('-', '_')}"
        print("Looking for table:", table_name)

        # Refresh metadata to make sure we have the latest tables
        metadata.reflect(bind=engine)

        if table_name not in metadata.tables:
            raise HTTPException(status_code=404, detail="Table not found")

        table = Table(table_name, metadata, autoload_with=engine)
        query = select(table).limit(20)

        print("Running query:", query)
        rows = await database.fetch_all(query)
        print("Rows fetched:", len(rows))

        sample_rows = [dict(row._mapping) for row in rows]
        columns = table.columns.keys()
        print("Columns:", columns)

        description_col = detect_description_column(columns, sample_rows)
        print("Detected description column:", description_col)

        return {"description_column": description_col}

    except Exception as e:
        print("Error in get_description_column:", e)
        raise HTTPException(status_code=500, detail=str(e))


# Uvicorn entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
