from fastapi import File, UploadFile,HTTPException,APIRouter
from fastapi.responses import JSONResponse
import uuid,os,shutil
import pandas as pd


from backend.utils.cleaning import filter_meaningful_rows
from backend.models import users
from backend.database import database

router = APIRouter()

UPLOAD_DIR = "app_data/uploaded_pdfs"
TABLES_DIR = "app_data/extracted_tables"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

@router.post("/upload-pdf/")
async def upload_pdf(user_id : str,file: UploadFile = File(...)):
    pdf_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{pdf_id}.pdf")
    
    query = users.select().where(users.c.user_id == user_id)
    user = await database.fetch_one(query)
    

    
    if not user:
        raise HTTPException(status_code=404,detail="User not found")
    
    print("Detected Bank:", user["bank_name"])
    bank_name = user["bank_name"].lower()
    print(bank_name)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"Saved PDF to {file_path}")
        
        print("Attempting to import parser...")
        parser_module = __import__(f"backend.parsers.{bank_name}_parser",fromlist=["process"])
        df_combined = parser_module.process(file_path)
        print("Successfully imported parser module.")

        df_combined.to_csv(os.path.join(TABLES_DIR, f"{pdf_id}.csv"), index=False)

        return {"pdf_id": pdf_id}
    
    except ModuleNotFoundError:
        raise HTTPException(status_code=400,detail=f"No parser available for {bank_name}")

    except Exception as e:
        print("PDF processing failed:", e)
        raise HTTPException(status_code=500, detail="Failed to process PDF")


@router.get("/tables/{pdf_id}")
def get_tables(pdf_id: str):
    try:
        table_path = os.path.join("app_data/extracted_tables", f"{pdf_id}.csv")
        print("Looking for:", table_path)

        if not os.path.exists(table_path):
            return JSONResponse(status_code=404, content={"error": "Table file not found"})

        df = pd.read_csv(table_path)

        if df.empty:
            return JSONResponse(status_code=204, content={"error": "No table data found"})

        # 🧹 Clean: remove infinite values, fill NaN
        df.replace([float('inf'), float('-inf')], None, inplace=True)
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].fillna("")


        # 🧹 Remove duplicates
        df.drop_duplicates(inplace=True)

        # Convert to list of dicts
        rows = df.to_dict(orient="records")
        rows = filter_meaningful_rows(rows)

        return rows

    except Exception as e:
        print("Error loading table:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

