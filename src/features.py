import numpy as np
import pandas as pd


def classify_account_size(employees: float) -> str:
    if employees >= 5000:
        return "Strategic Enterprise"
    if employees >= 1000:
        return "Enterprise"
    if employees >= 250:
        return "Mid-Market"
    return "SMB"


def classify_revenue_band(revenue: float) -> str:
    if revenue >= 5000:
        return "High Revenue"
    if revenue >= 1000:
        return "Medium Revenue"
    if revenue >= 250:
        return "Developing Revenue"
    return "Low Revenue"


def engineer_account_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["account_size_segment"] = df["employees"].apply(classify_account_size)
    df["revenue_band"] = df["revenue"].apply(classify_revenue_band)

    df["revenue_per_employee"] = np.where(
        df["employees"] > 0,
        df["revenue"] / df["employees"],
        0
    )

    df["company_age"] = 2026 - df["year_established"]

    df["is_parent_account"] = df["account"].isin(df["subsidiary_of"])
    df["is_subsidiary"] = df["subsidiary_of"] != "Independent"

    df["is_priority_sector"] = df["sector"].str.lower().isin([
        "finance",
        "technology",
        "software",
        "telecommunications",
        "services"
    ])

    df["international_account"] = df["office_location"] != "United States"

    df["account_priority_score"] = (
        df["is_priority_sector"].astype(int) * 30
        + df["revenue_band"].map({
            "High Revenue": 35,
            "Medium Revenue": 25,
            "Developing Revenue": 12,
            "Low Revenue": 5
        }).fillna(0)
        + df["account_size_segment"].map({
            "Strategic Enterprise": 25,
            "Enterprise": 18,
            "Mid-Market": 10,
            "SMB": 4
        }).fillna(0)
        + df["is_parent_account"].astype(int) * 10
    ).clip(0, 100)

    return df


def summarize_features(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "sectors": df["sector"].value_counts().head(8).to_dict(),
        "account_size_distribution": df["account_size_segment"].value_counts().to_dict(),
        "revenue_band_distribution": df["revenue_band"].value_counts().to_dict(),
        "priority_accounts": int((df["account_priority_score"] >= 70).sum()),
        "international_accounts": int(df["international_account"].sum()),
        "subsidiary_accounts": int(df["is_subsidiary"].sum()),
        "average_priority_score": round(float(df["account_priority_score"].mean()), 2),
    }
