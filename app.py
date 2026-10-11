import pandas as pd
import plotly.express as px
import streamlit as st

from src.main import run_war_room


st.set_page_config(page_title="RevenueOps Agent Control Tower", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #32104d 0, #12091f 35%, #070711 100%);
        color: #fff7ff;
    }
    [data-testid="stHeader"] { background: transparent; }
    .agent-step {
        padding: 12px 14px;
        margin-bottom: 10px;
        border-left: 4px solid #ff5bbd;
        border-radius: 12px;
        background: rgba(255,255,255,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("RevenueOps Agent Control Tower")
st.caption("Goal-driven agentic workflow for CRM data engineering, tool planning, revenue-leak investigation, action cards, relationship mapping, and human review.")

if "result" not in st.session_state:
    st.session_state["goal"] = "Find revenue leakage, pipeline risks, data quality issues, and accounts needing GTM action."
    st.session_state["result"] = run_war_room(st.session_state["goal"])

goal = st.text_area(
    "Investigation goal",
    value=st.session_state.get("goal", "Find revenue leakage, pipeline risks, data quality issues, and accounts needing GTM action."),
    height=85,
)

if st.button("Run Planner Agent", type="primary"):
    st.session_state["goal"] = goal
    st.session_state["result"] = run_war_room(goal)

result = st.session_state["result"]
accounts = result["accounts_df"]
revenue = result["revenue_df"]
cards = pd.DataFrame(result["action_cards"])
review = pd.DataFrame(result["human_review_queue"])
summary = result["feature_summary"]
graph = result["relationship_graph"]

st.markdown("### Planner Output")
plan_col1, plan_col2 = st.columns([0.75, 1.25])
with plan_col1:
    st.write("**Selected tools**")
    for tool in result["selected_tools"]:
        st.code(tool)
with plan_col2:
    st.write("**Agent answer**")
    st.write(result["agent_answer"])

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Accounts", summary["rows"])
col2.metric("Opportunities", len(revenue))
col3.metric("Action cards", len(cards))
col4.metric("Human review", len(review))
col5.metric("Graph edges", len(graph.get("edges", [])))

st.divider()

mode_options = ["All"] + sorted(cards["mode"].dropna().unique().tolist()) if not cards.empty else ["All"]
selected_mode = st.selectbox("Investigation mode", mode_options)
selected_decision = st.selectbox("Decision lane", ["All", "Human Review", "Needs Enrichment", "Auto-Recommend"])

filtered_cards = cards.copy()
if selected_mode != "All":
    filtered_cards = filtered_cards[filtered_cards["mode"] == selected_mode]
if selected_decision != "All":
    filtered_cards = filtered_cards[filtered_cards["decision"] == selected_decision]

left, right = st.columns([1.1, 0.9])

with left:
    st.subheader("Action Card Board")
    if not filtered_cards.empty:
        st.dataframe(filtered_cards, use_container_width=True, hide_index=True)
    else:
        st.info("No action cards for this filter.")

with right:
    st.subheader("Risk Distribution")
    if not cards.empty:
        fig = px.histogram(
            cards,
            x="mode",
            color="severity",
            barmode="group",
            color_discrete_map={"High": "#ff4f8b", "Medium": "#a855f7", "Low": "#38bdf8"},
        )
        fig.update_layout(height=390, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff7ff")
        st.plotly_chart(fig, use_container_width=True)

tabs = st.tabs(["Tool Results", "Revenue Graph", "What-If Simulator", "Human Review", "Data Quality", "Ask The Agent", "Report"])

with tabs[0]:
    st.subheader("Executed Tool Results")
    for tool_name, records in result["tool_results"].items():
        with st.expander(f"{tool_name}: {len(records)} evidence records", expanded=True):
            if records:
                st.dataframe(pd.DataFrame(records).head(80), use_container_width=True, hide_index=True)
            else:
                st.info("No evidence records returned by this tool.")

with tabs[1]:
    st.subheader("Revenue Relationship Graph")
    st.write(f"Nodes: {len(graph.get('nodes', []))} | Edges: {len(graph.get('edges', []))}")
    st.dataframe(pd.DataFrame(graph.get("nodes", [])), use_container_width=True, hide_index=True)
    st.dataframe(pd.DataFrame(graph.get("edges", [])), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("What-If Revenue Thresholds")
    value_threshold = st.slider("High-value product threshold", 500, 10000, 3000, 250)
    cycle_threshold = st.slider("Stuck pipeline days", 30, 250, 90, 10)
    what_if = revenue[(revenue["is_open"]) & (revenue["sales_price"] >= value_threshold) & (revenue["deal_cycle_days"] >= cycle_threshold)]
    st.metric("Potential stuck high-value opportunities", len(what_if))
    st.dataframe(
        what_if[["opportunity_id", "account", "product", "sales_agent", "deal_stage", "sales_price", "deal_cycle_days"]].head(100),
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    st.subheader("Human Review Console")
    if review.empty:
        st.success("No records routed to human review.")
    else:
        review["review_status"] = "Open"
        st.data_editor(review, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Data Quality Findings")
    st.json(result["quality_issues"])
    st.dataframe(
        accounts[["account", "sector", "revenue", "employees", "office_location", "subsidiary_of", "account_priority_score"]],
        use_container_width=True,
        hide_index=True,
    )

with tabs[5]:
    st.subheader("Ask The Agent")
    st.write("Type a new goal at the top and click **Run Planner Agent**. The planner will select tools and rerun the investigation.")
    candidates = filtered_cards if not filtered_cards.empty else cards
    st.write("Current evidence-backed answer:")
    for _, row in candidates.head(8).iterrows():
        st.write(f"- **{row['account']}**: {row['signal']} ({row['severity']}). {row['recommended_action']}")

with tabs[6]:
    st.subheader("Audit Report")
    for event in result["audit_trace"]:
        st.markdown(f"<div class='agent-step'>{event}</div>", unsafe_allow_html=True)
    st.markdown(result["final_report"])
    st.download_button("Download report", result["final_report"], "revenueops_agent_control_tower_report.md")
