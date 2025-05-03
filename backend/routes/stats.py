from fastapi import APIRouter, HTTPException, Query
import os
import pandas as pd
from backend.database import database
from backend.models import users
from backend.utils.categorizer import categorize_description, get_week_of_month
import importlib

router = APIRouter()

def money_to_float(x):
    x = str(x).replace("$", "").replace(",", "").strip()
    return float(x) if x.replace('.', '', 1).isdigit() else 0.0

async def load_dataframe(pdf_id: str, user_id: str) -> pd.DataFrame:
    # Get bank name from user
    query = users.select().where(users.c.user_id == user_id)
    user = await database.fetch_one(query)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bank_name = user["bank_name"].lower()

    # Load the PDF's table from CSV
    path = os.path.join("app_data/extracted_tables", f"{pdf_id}.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF data not found")

    df = pd.read_csv(path).fillna("")

    try:
        # Import bank-specific parser and run cleanup if available
        parser_module = __import__(f"backend.parsers.{bank_name}_parser", fromlist=["clean_for_stats"])
        if hasattr(parser_module, "clean_for_stats"):
            df = parser_module.clean_for_stats(df)
    except ModuleNotFoundError:
        raise HTTPException(status_code=400, detail=f"No parser available for {bank_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bank-specific parsing error: {str(e)}")

    return df


@router.get("/stats/{pdf_id}")
async def get_bank_statement_stats(pdf_id: str, user_id: str = Query(...)):
    df = await load_dataframe(pdf_id, user_id)

    df["Withdrawals"] = df["Withdrawals"].apply(money_to_float)
    df["Deposits"] = df["Deposits"].apply(money_to_float)
    df["Category"] = df["Description"].apply(categorize_description)

    category_summary = (
        df.groupby("Category")["Withdrawals"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    essential_categories = ["Groceries", "Utilities", "Healthcare", "Education", "Insurance", "Fuel", "Rent"]
    df["SpendingType"] = df["Category"].apply(lambda cat: "Essential" if cat in essential_categories else "Non-Essential")

    essential_summary = (
        df.groupby("SpendingType")["Withdrawals"]
        .sum()
        .to_dict()
    )

    total_withdrawals = df["Withdrawals"].sum()
    total_deposits = df["Deposits"].sum()
    
    income_vs_expense_ratio = (
        round(total_deposits / total_withdrawals, 2)
        if total_withdrawals != 0 else None
    )

    return {
        "total_withdrawals": total_withdrawals,
        "total_deposits": total_deposits,
        "category_wise_spending": category_summary,
        "essential_vs_nonessential": essential_summary,
        "income_vs_expense_ratio": income_vs_expense_ratio
    }




@router.get("/weekly-trends/{pdf_id}")
async def get_weekly_trends(pdf_id: str, user_id: str = Query(...)):
    # Load the DataFrame from CSV
    df = await load_dataframe(pdf_id, user_id)

    # Fetch the user's bank
    query = users.select().where(users.c.user_id == user_id)
    user = await database.fetch_one(query)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bank_name = user["bank_name"].lower()
    print(f"Generating weekly trends for bank: {bank_name}")

    try:
        # Dynamically import the bank-specific parser module
        parser_module = importlib.import_module(f"backend.parsers.{bank_name}_parser")

        # Call the function to generate weekly trends
        if hasattr(parser_module, "prepare_weekly_trends"):
            result = parser_module.prepare_weekly_trends(df)
            return result
        else:
            raise HTTPException(status_code=500, detail="Bank-specific weekly trends function not found.")

    except ModuleNotFoundError:
        raise HTTPException(status_code=400, detail=f"No parser available for {bank_name}")
    except Exception as e:
        print("Error in weekly trend generation:", e)
        raise HTTPException(status_code=500, detail="Failed to generate weekly trends.")
