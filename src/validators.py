import pandas as pd


def validate_accounts(df: pd.DataFrame) -> list[dict]:
    issues = []
    required_columns = [
        "account",
        "sector",
        "year_established",
        "revenue",
        "employees",
        "office_location",
        "subsidiary_of",
    ]

    for column in required_columns:
        if column not in df.columns:
            issues.append({
                "severity": "High",
                "issue": "Missing required column",
                "field": column,
                "evidence": f"{column} is not present in the account dataset.",
            })

    if issues:
        return issues

    missing_names = df[df["account"].astype(str).str.strip().eq("")]
    if len(missing_names):
        issues.append({
            "severity": "High",
            "issue": "Missing account names",
            "field": "account",
            "evidence": f"{len(missing_names)} rows have blank account names.",
        })

    duplicate_names = df[df["account"].duplicated(keep=False)]
    if len(duplicate_names):
        issues.append({
            "severity": "Medium",
            "issue": "Duplicate account records",
            "field": "account",
            "evidence": f"{duplicate_names['account'].nunique()} account names appear more than once.",
        })

    typo_sector = df[df["sector"].astype(str).str.lower().eq("technolgy")]
    if len(typo_sector):
        issues.append({
            "severity": "Low",
            "issue": "Sector normalization required",
            "field": "sector",
            "evidence": "Sector value 'technolgy' should be normalized to 'technology'.",
        })

    invalid_revenue = df[df["revenue"] <= 0]
    if len(invalid_revenue):
        issues.append({
            "severity": "Medium",
            "issue": "Invalid revenue values",
            "field": "revenue",
            "evidence": f"{len(invalid_revenue)} accounts have non-positive revenue.",
        })

    invalid_employees = df[df["employees"] <= 0]
    if len(invalid_employees):
        issues.append({
            "severity": "Medium",
            "issue": "Invalid employee counts",
            "field": "employees",
            "evidence": f"{len(invalid_employees)} accounts have non-positive employee count.",
        })

    future_established = df[df["year_established"] > 2026]
    if len(future_established):
        issues.append({
            "severity": "Medium",
            "issue": "Invalid establishment year",
            "field": "year_established",
            "evidence": f"{len(future_established)} accounts have a future establishment year.",
        })

    return issues
