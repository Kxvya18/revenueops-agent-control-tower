import pandas as pd


def detect_revenue_signals(df: pd.DataFrame) -> list[dict]:
    signals = []

    for _, row in df.iterrows():
        account = row["account"]

        if row["employees"] >= 1000 and row["revenue"] < 250:
            signals.append({
                "account": account,
                "category": "Revenue leak risk",
                "severity": "High",
                "signal": "Large account with unusually low reported revenue",
                "evidence": f"{int(row['employees'])} employees with revenue {row['revenue']}.",
                "recommended_action": "Validate account revenue and check whether opportunity records are missing.",
            })

        if row["is_priority_sector"] and row["account_priority_score"] >= 70:
            signals.append({
                "account": account,
                "category": "Priority GTM account",
                "severity": "Medium",
                "signal": "High-priority sector and strong account profile",
                "evidence": f"{row['sector']} account with priority score {round(row['account_priority_score'], 1)}.",
                "recommended_action": "Prioritize for account research, enrichment, and focused GTM follow-up.",
            })

        if row["is_subsidiary"]:
            signals.append({
                "account": account,
                "category": "Account hierarchy",
                "severity": "Low",
                "signal": "Subsidiary relationship detected",
                "evidence": f"Subsidiary of {row['subsidiary_of']}.",
                "recommended_action": "Review parent-child account mapping before campaign routing.",
            })

        if row["international_account"] and row["account_priority_score"] >= 55:
            signals.append({
                "account": account,
                "category": "Regional GTM routing",
                "severity": "Medium",
                "signal": "Priority account outside primary region",
                "evidence": f"Office location is {row['office_location']}.",
                "recommended_action": "Assign regional owner and verify localization requirements.",
            })

    return signals


def build_human_review_queue(signals: list[dict]) -> list[dict]:
    review = []
    for signal in signals:
        if signal["severity"] in {"High", "Medium"}:
            review.append({
                "account": signal["account"],
                "priority": signal["severity"],
                "reason": signal["signal"],
                "evidence": signal["evidence"],
                "next_step": signal["recommended_action"],
            })
    return review


def detect_pipeline_risks(revenue_df: pd.DataFrame, high_value_threshold: float = 3000, stuck_days: int = 90) -> list[dict]:
    signals = []

    won_low = revenue_df[(revenue_df["is_won"]) & (revenue_df["close_value"] < revenue_df["sales_price"] * 0.35)]
    for _, row in won_low.head(60).iterrows():
        signals.append({
            "account": row["account"],
            "opportunity_id": row["opportunity_id"],
            "category": "Revenue leakage",
            "severity": "High" if row["sales_price"] >= high_value_threshold else "Medium",
            "signal": "Won deal closed far below listed product price",
            "evidence": f"{row['product']} closed at {row['close_value']} against product price {row['sales_price']}.",
            "recommended_action": "Review discounting, bundling, or missing revenue attribution before forecasting.",
            "mode": "Revenue Leakage",
        })

    stuck_open = revenue_df[
        (revenue_df["is_open"])
        & (revenue_df["sales_price"] >= high_value_threshold)
        & (revenue_df["deal_cycle_days"] >= stuck_days)
    ]
    for _, row in stuck_open.head(60).iterrows():
        signals.append({
            "account": row["account"],
            "opportunity_id": row["opportunity_id"],
            "category": "Pipeline stagnation",
            "severity": "High",
            "signal": "High-value open opportunity has aged beyond threshold",
            "evidence": f"{row['deal_stage']} opportunity for {row['product']} has list value {row['sales_price']} and cycle age {int(row['deal_cycle_days'])} days.",
            "recommended_action": "Escalate to sales owner and request updated next step or close plan.",
            "mode": "Pipeline Stagnation",
        })

    lost_high = revenue_df[(revenue_df["is_lost"]) & (revenue_df["sales_price"] >= high_value_threshold)]
    for _, row in lost_high.head(60).iterrows():
        signals.append({
            "account": row["account"],
            "opportunity_id": row["opportunity_id"],
            "category": "Lost revenue review",
            "severity": "Medium",
            "signal": "High-value opportunity was lost",
            "evidence": f"{row['product']} opportunity lost with list value {row['sales_price']}.",
            "recommended_action": "Analyze loss reason, competitor risk, and reactivation timing.",
            "mode": "Revenue Leakage",
        })

    missing_mapping = revenue_df[revenue_df["sector"].isna() | revenue_df["manager"].isna()]
    for _, row in missing_mapping.head(40).iterrows():
        signals.append({
            "account": row["account"],
            "opportunity_id": row["opportunity_id"],
            "category": "Data quality",
            "severity": "Medium",
            "signal": "Opportunity is missing account or sales-team enrichment",
            "evidence": f"Missing account sector or manager mapping for opportunity {row['opportunity_id']}.",
            "recommended_action": "Fix CRM joins before downstream scoring or automated outreach.",
            "mode": "Data Quality",
        })

    return signals


def create_action_cards(signals: list[dict]) -> list[dict]:
    cards = []
    for index, signal in enumerate(signals, start=1):
        if signal["severity"] == "High":
            decision = "Human Review"
        elif signal["category"] in {"Data quality", "Account hierarchy"}:
            decision = "Needs Enrichment"
        else:
            decision = "Auto-Recommend"

        cards.append({
            "card_id": f"ACT-{index:04d}",
            "account": signal["account"],
            "opportunity_id": signal.get("opportunity_id", ""),
            "mode": signal.get("mode", signal["category"]),
            "severity": signal["severity"],
            "signal": signal["signal"],
            "evidence": signal["evidence"],
            "recommended_action": signal["recommended_action"],
            "decision": decision,
            "status": "Open",
        })
    return cards


def build_mode_summaries(cards: list[dict]) -> dict:
    summaries = {}
    for card in cards:
        mode = card["mode"]
        summaries.setdefault(mode, {"count": 0, "high": 0, "medium": 0, "low": 0})
        summaries[mode]["count"] += 1
        summaries[mode][card["severity"].lower()] += 1
    return summaries


def build_relationship_graph(accounts_df: pd.DataFrame, revenue_df: pd.DataFrame, max_edges: int = 90) -> dict:
    nodes = {}
    edges = []

    def add_node(node_id, label, node_type):
        nodes[node_id] = {"id": node_id, "label": str(label), "type": node_type}

    for _, row in accounts_df.head(60).iterrows():
        account_id = f"account::{row['account']}"
        add_node(account_id, row["account"], "Account")
        if row["is_subsidiary"]:
            parent_id = f"account::{row['subsidiary_of']}"
            add_node(parent_id, row["subsidiary_of"], "Parent Account")
            edges.append({"source": account_id, "target": parent_id, "relationship": "subsidiary_of"})

    for _, row in revenue_df.head(max_edges).iterrows():
        account_id = f"account::{row['account']}"
        product_id = f"product::{row['product']}"
        agent_id = f"agent::{row['sales_agent']}"
        add_node(account_id, row["account"], "Account")
        add_node(product_id, row["product"], "Product")
        add_node(agent_id, row["sales_agent"], "Sales Agent")
        edges.append({"source": account_id, "target": product_id, "relationship": row["deal_stage"]})
        edges.append({"source": account_id, "target": agent_id, "relationship": "owned_by"})

    return {"nodes": list(nodes.values()), "edges": edges[:max_edges]}
