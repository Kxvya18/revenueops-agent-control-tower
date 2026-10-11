from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

ACCOUNTS_PATH = RAW_DATA_DIR / "accounts.csv"
SALES_PIPELINE_PATH = RAW_DATA_DIR / "sales_pipeline.csv"
PRODUCTS_PATH = RAW_DATA_DIR / "products.csv"
SALES_TEAMS_PATH = RAW_DATA_DIR / "sales_teams.csv"
