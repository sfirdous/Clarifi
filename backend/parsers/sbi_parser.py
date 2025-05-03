import tabula
import pandas as pd
from backend.utils.categorizer import get_week_of_month

# Helper function to detect placeholder rows like {"Txn Date": "Txn Date", "Debit": "Debit", ...}
def is_placeholder_row(row):
    return all(v == k or v == "" for k, v in row.items())

# Convert string money values to float — handles commas, ₹, DR/CR tags
def money_to_float(x):
    x = str(x).replace(",", "").replace("₹", "").strip().upper()
    if "DR" in x or "CR" in x:
        x = x.replace("CR", "").replace("DR", "").strip()
    return float(x) if x.replace('.', '', 1).isdigit() else 0.0

# Clean and normalize columns for stats and categorization
def clean_for_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["Txn Date", "Description", "Debit", "Credit", "Balance"])

    # Rename to match stats module expectations
    df.rename(columns={
        "Txn Date": "Date",
        "Debit": "Withdrawals",
        "Credit": "Deposits"
    }, inplace=True)

    # Convert currency strings to float
    df["Withdrawals"] = df["Withdrawals"].apply(money_to_float)
    df["Deposits"] = df["Deposits"].apply(money_to_float)
    return df

# Prepare weekly trends from cleaned DataFrame
def prepare_weekly_trends(df: pd.DataFrame) -> list[dict]:
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"])

    # Grouping logic
    df["WeekOfMonth"] = df["Date"].apply(get_week_of_month)
    df["Month"] = df["Date"].dt.strftime("%Y-%m")
    df["WeekLabel"] = df["Month"] + " - Week " + df["WeekOfMonth"].astype(str)

    weekly = df.groupby("WeekLabel").agg({
        "Withdrawals": "sum",
        "Deposits": "sum"
    }).reset_index()

    return weekly.to_dict(orient="records")

# Merges multi-line SBI entries like Debit + Credit split across rows
def clean_sbi_entries(entries):
    cleaned_entries = []
    i = 0
    while i < len(entries):
        current = entries[i]

        if i + 1 < len(entries):
            next_entry = entries[i + 1]

            # Case 1: credit entry followed by debit-only
            if (
                current.get("Debit", "").strip() == "" and
                current.get("Credit", "").strip() != "" and
                next_entry.get("Debit", "").strip() == "-" and
                next_entry.get("Credit", "").strip() == ""
            ):
                merged = {
                    "Txn Date": current.get("Txn Date") or next_entry.get("Txn Date", ""),
                    "Value Date": current.get("Value Date") or next_entry.get("Value Date", ""),
                    "Description": current.get("Description", "") + " " + next_entry.get("Description", ""),
                    "Debit": "-",
                    "Credit": current["Credit"],
                    "Balance": next_entry.get("Balance", "")
                }
                cleaned_entries.append(merged)
                i += 2
                continue

            # Case 2: debit entry followed by credit-only
            elif (
                current.get("Debit", "").strip() == "-" and
                current.get("Credit", "").strip() == "" and
                next_entry.get("Debit", "").strip() == "" and
                next_entry.get("Credit", "").strip() != ""
            ):
                merged = {
                    "Txn Date": current.get("Txn Date") or next_entry.get("Txn Date", ""),
                    "Value Date": current.get("Value Date") or next_entry.get("Value Date", ""),
                    "Description": current.get("Description", "") + " " + next_entry.get("Description", ""),
                    "Debit": "-",
                    "Credit": next_entry["Credit"],
                    "Balance": next_entry.get("Balance", "")
                }
                cleaned_entries.append(merged)
                i += 2
                continue

        # Default — keep row as is
        cleaned_entries.append(current)
        i += 1

    return cleaned_entries

# Main processing function that runs Tabula and cleans everything
def process(file_path: str) -> pd.DataFrame:
    try:
        print("[SBI Parser] Extracting tables using Tabula....")

        # Read all tables using Tabula
        tables = tabula.read_pdf(
            file_path,
            pages='all',
            multiple_tables=True,
            guess=True,
            stream=True
        )

        if not tables:
            raise ValueError("No tables extracted from the PDF")

        print(f"[SBI Parser] Total Tables found: {len(tables)}")

        cleaned_tables = []

        # Column name mapping for unnamed columns
        column_mapping = {
            "Unnamed: 0": "Txn Date",
            "Unnamed: 1": "Value Date",
            "Unnamed: 2": "Description",
            "Unnamed: 3": "Debit",
            "Unnamed: 4": "Credit",
            "Unnamed: 5": "Balance"
        }

        for df in tables:
            df = df.copy()
            df.dropna(how="all", inplace=True)  # remove fully empty rows
            df.rename(columns={col: column_mapping.get(col, col) for col in df.columns}, inplace=True)
            df.fillna("", inplace=True)
            cleaned_tables.append(df)

        # Combine all pages
        combined_df = pd.concat(cleaned_tables, ignore_index=True)
        
        # Reset index to ensure uniqueness
        combined_df.reset_index(drop=True, inplace=True)

        # Merge rows with split transactions
        entries = combined_df.to_dict(orient="records")
        cleaned_entries = clean_sbi_entries(entries)

        # Remove rows with just column names or blanks
        cleaned_entries = [
            row for row in cleaned_entries
            if not is_placeholder_row(row)
        ]

        # Return as DataFrame
        return pd.DataFrame(cleaned_entries)

    except Exception as e:
        raise Exception(f"[SBI Parser] Failed to process: {str(e)}")
