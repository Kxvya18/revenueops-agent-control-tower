from typing import Any, TypedDict


class RevenueWarRoomState(TypedDict):
    user_goal: str
    investigation_plan: dict
    selected_tools: list[str]
    tool_results: dict
    evidence_store: list[dict]
    accounts_df: Any
    sales_pipeline_df: Any
    products_df: Any
    sales_teams_df: Any
    revenue_df: Any
    quality_issues: list[dict]
    feature_summary: dict
    risk_signals: list[dict]
    action_cards: list[dict]
    relationship_graph: dict
    mode_summaries: dict
    gtm_actions: list[dict]
    human_review_queue: list[dict]
    audit_trace: list[str]
    agent_answer: str
    final_report: str
