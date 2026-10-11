import pandas as pd


SECTOR_CORRECTIONS = {
    "technolgy": "technology"
}

LOCATION_CORRECTIONS = {
    "Philipines": "Philippines"
}


def normalize_key(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df


def load_accounts(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return standardize_columns(df)


def load_sales_pipeline(path: str) -> pd.DataFrame:
    return standardize_columns(pd.read_csv(path))


def load_products(path: str) -> pd.DataFrame:
    return standardize_columns(pd.read_csv(path))


def load_sales_teams(path: str) -> pd.DataFrame:
    return standardize_columns(pd.read_csv(path))


def clean_accounts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["account", "sector", "office_location", "subsidiary_of"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    df["sector"] = df["sector"].replace(SECTOR_CORRECTIONS)
    df["office_location"] = df["office_location"].replace(LOCATION_CORRECTIONS)

    for col in ["year_established", "revenue", "employees"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["subsidiary_of"] = df["subsidiary_of"].replace("", "Independent")

    return df


def clean_sales_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["opportunity_id", "sales_agent", "product", "account", "deal_stage"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    for col in ["engage_date", "close_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "close_value" in df.columns:
        df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce").fillna(0)

    df["account_key"] = df["account"].apply(normalize_key)
    df["product_key"] = df["product"].apply(normalize_key)

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["product", "series"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    if "sales_price" in df.columns:
        df["sales_price"] = pd.to_numeric(df["sales_price"], errors="coerce").fillna(0)
    df["product_key"] = df["product"].apply(normalize_key)
    return df


def clean_sales_teams(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["sales_agent", "manager", "regional_office"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    return df


def build_revenue_dataset(accounts: pd.DataFrame, pipeline: pd.DataFrame, products: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    accounts = accounts.copy()
    accounts["account_key"] = accounts["account"].apply(normalize_key)
    merged = pipeline.merge(accounts, on="account_key", how="left", suffixes=("", "_account"))
    merged["account"] = merged["account_account"].fillna(merged["account"])
    merged = merged.drop(columns=[col for col in ["account_account"] if col in merged.columns])
    merged = merged.merge(products, on="product_key", how="left", suffixes=("", "_product"))
    merged["product"] = merged["product_product"].fillna(merged["product"])
    merged = merged.drop(columns=[col for col in ["product_product"] if col in merged.columns])
    merged = merged.merge(teams, on="sales_agent", how="left")
    reference_date = pd.concat([merged["close_date"], merged["engage_date"]]).max()
    effective_close_date = merged["close_date"].fillna(reference_date)
    merged["deal_cycle_days"] = (effective_close_date - merged["engage_date"]).dt.days
    merged["deal_cycle_days"] = merged["deal_cycle_days"].fillna(-1)
    merged["is_won"] = merged["deal_stage"].str.lower().eq("won")
    merged["is_lost"] = merged["deal_stage"].str.lower().eq("lost")
    merged["is_open"] = ~merged["is_won"] & ~merged["is_lost"]
    merged["value_gap_to_product_price"] = merged["sales_price"] - merged["close_value"]
    return merged
