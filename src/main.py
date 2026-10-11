from src.graph import build_graph


def run_war_room(user_goal: str = "Find revenue leakage, pipeline risks, data quality issues, and accounts needing GTM action."):
    app = build_graph()
    initial_state = {
        "user_goal": user_goal,
        "investigation_plan": {},
        "selected_tools": [],
        "tool_results": {},
        "evidence_store": [],
        "accounts_df": None,
        "sales_pipeline_df": None,
        "products_df": None,
        "sales_teams_df": None,
        "revenue_df": None,
        "quality_issues": [],
        "feature_summary": {},
        "risk_signals": [],
        "action_cards": [],
        "relationship_graph": {},
        "mode_summaries": {},
        "gtm_actions": [],
        "human_review_queue": [],
        "audit_trace": [],
        "agent_answer": "",
        "final_report": "",
    }
    return app.invoke(initial_state)


if __name__ == "__main__":
    result = run_war_room()
    print(result["final_report"])
