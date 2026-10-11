import pandas as pd

from src.risk_rules import detect_pipeline_risks, detect_revenue_signals


def revenue_leakage_tool(state: dict) -> list[dict]:
    signals = detect_pipeline_risks(state["revenue_df"])
    return [item for item in signals if item.get("mode") == "Revenue Leakage"]


def pipeline_stagnation_tool(state: dict) -> list[dict]:
    signals = detect_pipeline_risks(state["revenue_df"])
    return [item for item in signals if item.get("mode") == "Pipeline Stagnation"]


def data_quality_tool(state: dict) -> list[dict]:
    findings = []
    for issue in state["quality_issues"]:
        findings.append({
            "account": "Multiple records",
            "category": "Data quality",
            "severity": issue["severity"],
            "signal": issue["issue"],
            "evidence": issue["evidence"],
            "recommended_action": "Fix data quality issue before automated routing or outreach.",
            "mode": "Data Quality",
        })
    return findings


def account_priority_tool(state: dict) -> list[dict]:
    signals = detect_revenue_signals(state["accounts_df"])
    return [
        item for item in signals
        if item["category"] in {"Priority GTM account", "Regional GTM routing", "Account hierarchy"}
    ]


def sales_rep_review_tool(state: dict) -> list[dict]:
    df = state["revenue_df"].copy()
    grouped = df.groupby(["sales_agent", "manager", "regional_office"], dropna=False).agg(
        opportunities=("opportunity_id", "count"),
        won=("is_won", "sum"),
        open_deals=("is_open", "sum"),
        total_closed_value=("close_value", "sum"),
        avg_cycle_days=("deal_cycle_days", "mean"),
    ).reset_index()
    grouped["win_rate"] = grouped["won"] / grouped["opportunities"]
    watch = grouped[(grouped["opportunities"] >= 40) & ((grouped["win_rate"] < 0.35) | (grouped["open_deals"] > grouped["opportunities"] * 0.3))]

    signals = []
    for _, row in watch.head(40).iterrows():
        signals.append({
            "account": str(row["sales_agent"]),
            "category": "Sales rep review",
            "severity": "Medium",
            "signal": "Sales agent has low win rate or elevated open pipeline load",
            "evidence": f"{int(row['opportunities'])} opportunities, win rate {row['win_rate']:.2f}, open deals {int(row['open_deals'])}, region {row['regional_office']}.",
            "recommended_action": "Review pipeline hygiene, follow-up cadence, and manager coaching needs.",
            "mode": "Sales Rep Review",
        })
    return signals


def product_risk_tool(state: dict) -> list[dict]:
    df = state["revenue_df"].copy()
    grouped = df.groupby(["product", "series"], dropna=False).agg(
        opportunities=("opportunity_id", "count"),
        won=("is_won", "sum"),
        lost=("is_lost", "sum"),
        open_deals=("is_open", "sum"),
        listed_price=("sales_price", "median"),
        closed_value=("close_value", "sum"),
    ).reset_index()
    grouped["loss_rate"] = grouped["lost"] / grouped["opportunities"]
    grouped["open_rate"] = grouped["open_deals"] / grouped["opportunities"]
    watch = grouped[(grouped["opportunities"] >= 50) & ((grouped["loss_rate"] > 0.35) | (grouped["open_rate"] > 0.25))]

    signals = []
    for _, row in watch.iterrows():
        signals.append({
            "account": str(row["product"]),
            "category": "Product risk",
            "severity": "Medium",
            "signal": "Product has elevated loss or open-pipeline rate",
            "evidence": f"{int(row['opportunities'])} opportunities, loss rate {row['loss_rate']:.2f}, open rate {row['open_rate']:.2f}, median price {row['listed_price']}.",
            "recommended_action": "Inspect pricing, positioning, and sales enablement for this product line.",
            "mode": "Product Risk",
        })
    return signals


TOOL_REGISTRY = {
    "revenue_leakage_tool": revenue_leakage_tool,
    "pipeline_stagnation_tool": pipeline_stagnation_tool,
    "data_quality_tool": data_quality_tool,
    "account_priority_tool": account_priority_tool,
    "sales_rep_review_tool": sales_rep_review_tool,
    "product_risk_tool": product_risk_tool,
}


def plan_tools(user_goal: str) -> dict:
    goal = user_goal.lower()
    selected = []

    if any(term in goal for term in ["leak", "discount", "lost", "money", "revenue"]):
        selected.extend(["revenue_leakage_tool", "product_risk_tool"])
    if any(term in goal for term in ["stuck", "pipeline", "proposal", "open", "follow"]):
        selected.append("pipeline_stagnation_tool")
    if any(term in goal for term in ["quality", "missing", "dirty", "join", "crm", "hygiene"]):
        selected.append("data_quality_tool")
    if any(term in goal for term in ["account", "prioritize", "gtm", "region", "subsidiary"]):
        selected.append("account_priority_tool")
    if any(term in goal for term in ["rep", "agent", "team", "manager", "performance"]):
        selected.append("sales_rep_review_tool")

    if not selected:
        selected = [
            "revenue_leakage_tool",
            "pipeline_stagnation_tool",
            "data_quality_tool",
            "account_priority_tool",
        ]

    selected = list(dict.fromkeys(selected))
    return {
        "goal": user_goal,
        "selected_tools": selected,
        "reason": "Tools were selected by matching the investigation goal to revenue, pipeline, CRM quality, account, product, and team-analysis capabilities.",
    }
