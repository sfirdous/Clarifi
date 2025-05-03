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