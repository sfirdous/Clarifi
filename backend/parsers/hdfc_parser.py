import tabula
import pandas as pd
from backend.utils.categorizer import get_week_of_month

def process(file_path: str) -> pd.DataFrame:
    try:
        print("[HDFC Parser] Extracting tables using Tabula...")

        tables = tabula.read_pdf(
            file_path,
            pages='all',
            multiple_tables=True,
            guess=True,
            stream=True
        )

        if not tables:
            raise ValueError("No tables extracted from the PDF.")

        print(f"[HDFC Parser] Total tables found: {len(tables)}")

        cleaned_tables = []

        for df in tables:
            df = df.copy()

            # Drop empty rows
            df.dropna(how="all", inplace=True)

            # Rename 'Unnamed: 0' to 'Narration' if it exists
            if "Unnamed: 0" in df.columns:
                df.rename(columns={"Unnamed: 0": "Narration"}, inplace=True)

            # Drop any duplicate narration columns like 'Narration.1', 'Narration.2', etc.
            df = df.loc[:, ~df.columns.str.contains(r"\.1$")]

            df.fillna("", inplace=True)
            cleaned_tables.append(df)

        # Combine all DataFrames
        combined_df = pd.concat(cleaned_tables, ignore_index=True)
        print(f"[HDFC Parser] Final cleaned shape: {combined_df.shape}")

        return combined_df

    except Exception as e:
        raise Exception(f"[HDFC Parser] Failed to process PDF: {str(e)}")


def clean_for_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"])
    df.rename(columns={"Narration": "Description", "Withdrawal Amt.": "Withdrawals", "Deposit Amt.": "Deposits"}, inplace=True)
    return df

def prepare_weekly_trends(df: pd.DataFrame) -> list[dict]:
    # Convert to datetime
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    df = df.dropna(subset=["Date"])

    # Convert money columns
    def money_to_float(x):
        x = str(x).replace(",", "").replace("₹", "").strip()
        return float(x) if x.replace('.', '', 1).isdigit() else 0.0

    df["Withdrawals"] = df["Withdrawals"].apply(money_to_float)
    df["Deposits"] = df["Deposits"].apply(money_to_float)

    # Week + Month labels
    df["WeekOfMonth"] = df["Date"].apply(get_week_of_month)
    df["Month"] = df["Date"].dt.strftime("%Y-%m")
    df["WeekLabel"] = df["Month"] + " - Week " + df["WeekOfMonth"].astype(str)

    weekly = df.groupby("WeekLabel").agg({
        "Withdrawals": "sum",
        "Deposits": "sum"
    }).reset_index()

    return weekly.to_dict(orient="records")
