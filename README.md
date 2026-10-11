# RevenueOps Agent Control Tower

RevenueOps Agent Control Tower is an agentic AI operations demo for CRM data engineering, revenue-risk detection, action-card generation, relationship mapping, and human-review routing.

The project uses CRM-style account, opportunity, product, and sales-team data to demonstrate how an AI operations system can move from raw CSV ingestion to evidence-backed revenue actions. The workflow is structured as multiple agent nodes rather than a single prompt so that every step remains inspectable and auditable.

## Workflow

```text
CRM CSVs
-> Data Engineer Agent
-> Data Quality Agent
-> Revenue Investigator Agent
-> GTM Strategy Agent
-> Risk Reviewer Agent
-> Report Writer Agent
```

## Capabilities

- Account data ingestion and schema standardization
- Cross-file entity joins across accounts, opportunities, products, and sales teams
- Category correction and numeric normalization
- Data quality validation
- Feature engineering for account size, revenue band, revenue per employee, company age, parent/subsidiary status, priority sector, and regional routing
- Revenue leakage, pipeline stagnation, discounting, lost-revenue, data-quality, and regional routing signals
- Action cards with Auto-Recommend, Needs Enrichment, and Human Review decision lanes
- Relationship graph preview across accounts, products, sales agents, and subsidiary links
- What-if threshold simulator in the Streamlit app
- Human-review console
- Agent audit trace
- Streamlit dashboard and no-install HTML dashboard

## Run

Generate the no-install HTML dashboard:

```bash
python dashboard.py
```

Open:

```text
outputs/war_room_dashboard.html
```

Run the optional Streamlit dashboard after installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For terminal output:

```bash
python -m src.main
```
