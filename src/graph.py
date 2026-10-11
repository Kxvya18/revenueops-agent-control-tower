try:
    from langgraph.graph import END, StateGraph
except ModuleNotFoundError:
    END = "__end__"
    StateGraph = None

from src.agent_state import RevenueWarRoomState
from src.agent_tools import TOOL_REGISTRY, plan_tools
from src.config import ACCOUNTS_PATH, PRODUCTS_PATH, SALES_PIPELINE_PATH, SALES_TEAMS_PATH
from src.etl import (
    build_revenue_dataset,
    clean_accounts,
    clean_products,
    clean_sales_pipeline,
    clean_sales_teams,
    load_accounts,
    load_products,
    load_sales_pipeline,
    load_sales_teams,
)
from src.features import engineer_account_features, summarize_features
from src.risk_rules import build_mode_summaries, build_relationship_graph, create_action_cards
from src.validators import validate_accounts


def data_engineer_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    accounts = engineer_account_features(clean_accounts(load_accounts(ACCOUNTS_PATH)))
    pipeline = clean_sales_pipeline(load_sales_pipeline(SALES_PIPELINE_PATH))
    products = clean_products(load_products(PRODUCTS_PATH))
    teams = clean_sales_teams(load_sales_teams(SALES_TEAMS_PATH))
    revenue = build_revenue_dataset(accounts, pipeline, products, teams)

    state["accounts_df"] = accounts
    state["sales_pipeline_df"] = pipeline
    state["products_df"] = products
    state["sales_teams_df"] = teams
    state["revenue_df"] = revenue
    state["feature_summary"] = summarize_features(accounts)
    state["relationship_graph"] = build_relationship_graph(accounts, revenue)
    state["audit_trace"].append(
        f"Data Engineer Agent loaded {len(accounts)} accounts, {len(pipeline)} opportunities, {len(products)} products, and {len(teams)} sales-team records, then built a joined revenue dataset with {len(revenue)} rows."
    )
    return state


def data_quality_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    issues = validate_accounts(state["accounts_df"])
    missing_account_join = int(state["revenue_df"]["sector"].isna().sum())
    missing_team_join = int(state["revenue_df"]["manager"].isna().sum())
    missing_product_join = int(state["revenue_df"]["sales_price"].isna().sum())

    if missing_account_join:
        issues.append({
            "severity": "High",
            "issue": "Opportunity account join failure",
            "field": "account",
            "evidence": f"{missing_account_join} opportunities did not match account master data.",
        })
    if missing_team_join:
        issues.append({
            "severity": "Medium",
            "issue": "Sales-team join failure",
            "field": "sales_agent",
            "evidence": f"{missing_team_join} opportunities did not match sales-team records.",
        })
    if missing_product_join:
        issues.append({
            "severity": "Medium",
            "issue": "Product join failure",
            "field": "product",
            "evidence": f"{missing_product_join} opportunities did not match product records.",
        })

    state["quality_issues"] = issues
    state["audit_trace"].append(
        f"Data Quality Agent completed schema, value, and cross-file join checks with {len(issues)} issue groups."
    )
    return state


def planner_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    plan = plan_tools(state["user_goal"])
    state["investigation_plan"] = plan
    state["selected_tools"] = plan["selected_tools"]
    state["audit_trace"].append(
        f"Planner Agent interpreted goal '{state['user_goal']}' and selected tools: {', '.join(state['selected_tools'])}."
    )
    return state


def tool_executor_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    tool_results = {}
    evidence = []

    for tool_name in state["selected_tools"]:
        tool = TOOL_REGISTRY[tool_name]
        result = tool(state)
        tool_results[tool_name] = result
        evidence.extend(result)
        state["audit_trace"].append(
            f"Tool Executor Agent ran {tool_name} and collected {len(result)} evidence records."
        )

    state["tool_results"] = tool_results
    state["evidence_store"] = evidence
    state["risk_signals"] = evidence
    return state


def reasoning_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    cards = create_action_cards(state["evidence_store"])
    state["action_cards"] = cards
    state["mode_summaries"] = build_mode_summaries(cards)
    state["gtm_actions"] = [
        {
            "account": card["account"],
            "priority": card["severity"],
            "action_type": card["mode"],
            "recommended_action": card["recommended_action"],
            "evidence": card["evidence"],
        }
        for card in cards
    ]

    high = sum(1 for card in cards if card["severity"] == "High")
    medium = sum(1 for card in cards if card["severity"] == "Medium")
    modes = ", ".join(sorted(state["mode_summaries"].keys())) if state["mode_summaries"] else "none"
    state["agent_answer"] = (
        f"For the goal '{state['user_goal']}', the agent selected {len(state['selected_tools'])} tools, "
        f"found {len(cards)} action cards, including {high} high-priority and {medium} medium-priority items. "
        f"The active investigation modes are: {modes}."
    )
    state["audit_trace"].append(
        f"Reasoning Agent synthesized {len(state['evidence_store'])} evidence records into {len(cards)} action cards and mode summaries."
    )
    return state


def risk_reviewer_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    review = [
        {
            "account": card["account"],
            "priority": card["severity"],
            "reason": card["signal"],
            "evidence": card["evidence"],
            "next_step": card["recommended_action"],
        }
        for card in state["action_cards"]
        if card["decision"] == "Human Review"
    ]
    state["human_review_queue"] = review
    state["audit_trace"].append(
        f"Risk Reviewer Agent routed {len(review)} high-risk records to the human review console."
    )
    return state


def report_writer_agent(state: RevenueWarRoomState) -> RevenueWarRoomState:
    high = sum(1 for item in state["risk_signals"] if item["severity"] == "High")
    medium = sum(1 for item in state["risk_signals"] if item["severity"] == "Medium")
    low = sum(1 for item in state["risk_signals"] if item["severity"] == "Low")
    graph = state["relationship_graph"]

    report = [
        "# RevenueOps Agent Control Tower Report",
        "",
        "## User Goal",
        state["user_goal"],
        "",
        "## Agent Plan",
        f"Selected tools: {', '.join(state['selected_tools'])}",
        state["investigation_plan"]["reason"],
        "",
        "## Executive Summary",
        state["agent_answer"],
        f"The workflow analyzed {state['feature_summary']['rows']} account records and {len(state['revenue_df'])} opportunity records after data engineering and entity joins.",
        f"Detected evidence: {high} high, {medium} medium, and {low} low-priority items.",
        "",
        "## Investigation Modes",
        str(state["mode_summaries"]),
        "",
        "## Relationship Graph",
        f"Graph contains {len(graph.get('nodes', []))} nodes and {len(graph.get('edges', []))} edges across accounts, products, agents, and parent/subsidiary links.",
        "",
        "## Top Action Cards",
    ]

    for card in state["action_cards"][:12]:
        report.append(
            f"- {card['card_id']} | {card['account']} [{card['severity']} / {card['decision']}]: {card['recommended_action']} Evidence: {card['evidence']}"
        )

    report.extend([
        "",
        "## Data Quality Issues",
        str(state["quality_issues"] if state["quality_issues"] else "No major blocking issues detected."),
        "",
        "## Agent Audit Trace",
    ])
    report.extend([f"- {event}" for event in state["audit_trace"]])

    state["final_report"] = "\n".join(report)
    state["audit_trace"].append("Report Writer Agent generated final evidence-backed report.")
    return state


def build_graph():
    nodes = [
        data_engineer_agent,
        data_quality_agent,
        planner_agent,
        tool_executor_agent,
        reasoning_agent,
        risk_reviewer_agent,
        report_writer_agent,
    ]

    if StateGraph is None:
        class LocalAgentWorkflow:
            def invoke(self, state):
                for node in nodes:
                    state = node(state)
                return state

        return LocalAgentWorkflow()

    graph = StateGraph(RevenueWarRoomState)
    for node in nodes:
        graph.add_node(node.__name__, node)

    graph.set_entry_point("data_engineer_agent")
    graph.add_edge("data_engineer_agent", "data_quality_agent")
    graph.add_edge("data_quality_agent", "planner_agent")
    graph.add_edge("planner_agent", "tool_executor_agent")
    graph.add_edge("tool_executor_agent", "reasoning_agent")
    graph.add_edge("reasoning_agent", "risk_reviewer_agent")
    graph.add_edge("risk_reviewer_agent", "report_writer_agent")
    graph.add_edge("report_writer_agent", END)

    return graph.compile()
