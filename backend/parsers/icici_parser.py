import tabula
import pandas as pd
from backend.utils.categorizer import get_week_of_month

def remove_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    # Drop rows where 'S No.' equals the string "S No." or is NaN
    df = df[df["S No."].apply(lambda x: str(x).strip() != "S No." and str(x).strip().lower() != "nan")]
    return df

def money_to_float(x):
    x = str(x).replace(",", "").replace("\r", "").strip().upper()
    if "CR" in x or "DR" in x:
        x = x.replace("CR", "").replace("DR", "").strip()
    return float(x) if x.replace('.', '', 1).isdigit() else 0.0


def process(file_path: str) -> pd.DataFrame:
    try:
        print("[ICICI Parser] Extracting tables using Tabula...")

        tables = tabula.read_pdf(
            file_path,
            pages='all',
            multiple_tables=True,
            guess=True,
            lattice=True
        )

        if not tables:
            raise ValueError("No tables extracted from the PDF")

        print(f"[ICICI Parser] Total tables found: {len(tables)}")

        cleaned_tables = []

        for idx, df in enumerate(tables):
            df = df.copy()
            df.dropna(how="all", inplace=True)

            # Log shape and columns to debug if needed
            print(f"  - Table {idx + 1} shape: {df.shape}, columns: {df.columns.tolist()}")

            # Define expected columns
            expected_columns = [
                "S No.", "Value Date", "Transaction Date", "Cheque Number",
                "Transaction Remarks", "Withdrawal Amount (INR)",
                "Deposit Amount (INR)", "Balance (INR )"
            ]

            # Handle column header mismatch
            if len(df.columns) == len(expected_columns):
                df.columns = expected_columns
            elif len(df.columns) > len(expected_columns):
                # Truncate extra columns
                df.columns = expected_columns + [f"Extra_{i}" for i in range(len(df.columns) - len(expected_columns))]
            else:
                print(f"[ICICI Parser] Skipping table {idx + 1} due to unexpected column count: {len(df.columns)}")
                continue

            df.fillna("", inplace=True)
            cleaned_tables.append(df)

        if not cleaned_tables:
            raise ValueError("No usable tables found after cleaning.")

        combined_df = pd.concat(cleaned_tables, ignore_index=True)

        # Remove header rows
        combined_df = remove_header_rows(combined_df)

    


        print(f"[ICICI Parser] Final cleaned shape: {combined_df.shape}")
        return combined_df

    except Exception as e:
        raise Exception(f"[ICICI Parser] Failed to process PDF: {str(e)}")


def clean_for_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=[
        "Transaction Date", "Transaction Remarks",
        "Withdrawal Amount (INR)", "Deposit Amount (INR)", "Balance (INR )"
    ])

    df.rename(columns={
        "Transaction Date": "Date",
        "Transaction Remarks": "Description",
        "Withdrawal Amount (INR)": "Withdrawals",
        "Deposit Amount (INR)": "Deposits"
    }, inplace=True)

    return df


def prepare_weekly_trends(df: pd.DataFrame) -> list[dict]:
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Date"])

    df["Withdrawals"] = df["Withdrawals"].apply(money_to_float)
    df["Deposits"] = df["Deposits"].apply(money_to_float)

    df["WeekOfMonth"] = df["Date"].apply(get_week_of_month)
    df["Month"] = df["Date"].dt.strftime("%Y-%m")
    df["WeekLabel"] = df["Month"] + " - Week " + df["WeekOfMonth"].astype(str)

    weekly = df.groupby("WeekLabel").agg({
        "Withdrawals": "sum",
        "Deposits": "sum"
    }).reset_index()

    return weekly.to_dict(orient="records")
