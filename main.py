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
                guess=True,
                stream=True  
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
        
       
        # Try to detect header and update column names
        df_combined, header_mapping = map_columns_using_header(df_combined)
        
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

        # 🧹 Clean: remove infinite values, fill NaN
        df.replace([float('inf'), float('-inf')], None, inplace=True)
        df.fillna("", inplace=True)

        # 🧹 Remove duplicates
        df.drop_duplicates(inplace=True)

        # Convert to list of dicts
        rows = df.to_dict(orient="records")
        rows = filter_meaningful_rows(rows)

        return rows

    except Exception as e:
        print("Error loading table:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.get("/stats/{pdf_id}")
async def get_bank_statement_stats(pdf_id: str):
    path = os.path.join("extracted_tables", f"{pdf_id}.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Data not found")

    df = pd.read_csv(path).fillna("")

    # 🛑 Remove duplicate rows based on all key columns
    df = df.drop_duplicates(subset=["Date", "Description", "Withdrawals", "Deposits", "Balance"])

    def money_to_float(x):
        x = str(x).replace("$", "").replace(",", "").strip()
        return float(x) if x.replace('.', '', 1).isdigit() else 0.0

    df["Withdrawals"] = df["Withdrawals"].apply(money_to_float)
    df["Deposits"] = df["Deposits"].apply(money_to_float)
    df["Category"] = df["Description"].apply(categorize_description)

    category_summary = (
        df.groupby("Category")["Withdrawals"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    return {
        "total_withdrawals": df["Withdrawals"].sum(),
        "total_deposits": df["Deposits"].sum(),
        "category_wise_spending": category_summary
    }


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


def map_columns_using_header(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Detects header row and renames generic col_1, col_2... to actual headers like Date, Description, etc.
    Returns the modified DataFrame and a mapping dictionary.
    """
    for i, row in df.iterrows():
        values = list(row)
        non_empty = [v for v in values if str(v).strip()]
        if len(non_empty) >= 3:
            header_mapping = {f"col_{j+1}": str(val).strip() for j, val in enumerate(values)}
            df = df.drop(index=i).reset_index(drop=True)
            df.rename(columns=header_mapping, inplace=True)
            return df, header_mapping

    return df, {}

def filter_meaningful_rows(rows: list[dict], threshold: int = 2) -> list[dict]:
    """
    Filters out rows with less than `threshold` meaningful (non-empty, non-trivial) fields,
    and removes 'page_number' from final output.
    """
    cleaned = []
    for row in rows:
        # Remove 'page_number' for processing and final result
        row_copy = {k: v.strip() for k, v in row.items() if k != "page_number"}
        
        # Count non-empty values with more than 3 characters
        non_empty = [v for v in row_copy.values() if v and len(v) > 3]

        if len(non_empty) >= threshold:
            cleaned.append(row_copy)
    
    return cleaned


def get_unique_descriptions(table_data: list[dict], description_key: str = "Description") -> list[str]:
    """
    Extracts unique, non-empty values from the 'Description' column.
    
    Args:
        table_data: List of dictionaries representing table rows.
        description_key: The column name to extract descriptions from.

    Returns:
        A sorted list of unique descriptions.
    """
    descriptions = set()
    for row in table_data:
        value = row.get(description_key, "").strip()
        if value:  # Non-empty check
            descriptions.add(value)
    return sorted(descriptions)


def categorize_description(desc: str) -> str:
    desc = desc.lower()

    categories = {
        "Groceries": ["grocery", "supermarket", "mart"],
        "Utilities": ["electric", "water", "gas", "bill", "maintenance"],
        "Entertainment": ["movie", "netflix", "prime", "streaming", "music", "subscription"],
        "Dining": ["restaurant", "coffee", "cafe", "dining", "food"],
        "Travel": ["uber", "flight", "air", "train", "taxi"],
       
        "ATM Withdrawals": ["atm", "cash withdrawal"],
        "Insurance": ["insurance", "premium"],
        "Fitness": ["gym", "fitness"],
        "Misc": []  # fallback if nothing matches
    }

    for category, keywords in categories.items():
        if any(keyword in desc for keyword in keywords):
            return category

    return "Misc"

      
# Uvicorn entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
