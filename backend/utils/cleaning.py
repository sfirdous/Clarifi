import pandas as pd

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
    cleaned = []
    for row in rows:
        row_copy = {
            k: str(v).strip() for k, v in row.items() if k != "page_number"
        }

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