from html import escape
from pathlib import Path

from src.main import run_war_room


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "war_room_dashboard.html"


def rows(records, columns, limit=120):
    body = []
    for record in records[:limit]:
        body.append("<tr>" + "".join(f"<td>{escape(str(record.get(col, '')))}</td>" for col in columns) + "</tr>")
    return "\n".join(body)


def bars(cards):
    counts = {}
    for card in cards:
        counts.setdefault(card["mode"], 0)
        counts[card["mode"]] += 1
    max_count = max(counts.values()) if counts else 1
    out = []
    for mode, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        width = int((count / max_count) * 100)
        out.append(f"<div class='bar'><span>{escape(mode)}</span><i><b style='width:{width}%'></b></i><strong>{count}</strong></div>")
    return "".join(out)


def graph_preview(graph):
    nodes = graph.get("nodes", [])[:24]
    if not nodes:
        return ""
    chips = []
    for node in nodes:
        chips.append(f"<span class='node {escape(node['type']).lower().replace(' ', '-')}'>{escape(node['label'])}<small>{escape(node['type'])}</small></span>")
    return "".join(chips)


def render_dashboard():
    result = run_war_room()
    summary = result["feature_summary"]
    cards = result["action_cards"]
    review = result["human_review_queue"]
    graph = result["relationship_graph"]
    report = result["final_report"]

    card_columns = ["card_id", "account", "opportunity_id", "mode", "severity", "decision", "signal", "evidence", "recommended_action"]
    review_columns = ["account", "priority", "reason", "evidence", "next_step"]

    high = sum(1 for card in cards if card["severity"] == "High")
    medium = sum(1 for card in cards if card["severity"] == "Medium")
    low = sum(1 for card in cards if card["severity"] == "Low")

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RevenueOps Agent Control Tower</title>
<style>
:root {{ --bg:#070711; --panel:rgba(255,255,255,.075); --line:rgba(255,255,255,.16); --text:#fff7ff; --muted:#cbbdda; --pink:#ff5bbd; --cyan:#52e3ff; --violet:#a855f7; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:radial-gradient(circle at 16% 8%, rgba(255,91,189,.34), transparent 28%), radial-gradient(circle at 88% 20%, rgba(82,227,255,.18), transparent 26%), linear-gradient(135deg,#140823,#070711 55%,#18092b); color:var(--text); }}
main {{ width:min(1220px, calc(100vw - 32px)); margin:0 auto; padding:44px 0 70px; }}
.hero {{ display:grid; grid-template-columns:1.1fr .9fr; gap:24px; align-items:center; min-height:360px; }}
h1 {{ margin:0 0 18px; font-size:clamp(44px,7vw,88px); line-height:.9; letter-spacing:-.05em; }}
h2 {{ margin:0 0 18px; font-size:28px; }}
p {{ color:var(--muted); font-size:18px; line-height:1.6; }}
.panel, section {{ border:1px solid var(--line); background:var(--panel); border-radius:26px; padding:22px; box-shadow:0 24px 70px rgba(0,0,0,.26); backdrop-filter:blur(18px); }}
.orb {{ height:340px; border-radius:36px; overflow:hidden; position:relative; background:radial-gradient(circle at 52% 42%, rgba(168,85,247,.9), rgba(36,22,78,.94) 42%, rgba(7,7,17,.96) 75%); border:1px solid var(--line); }}
.orb:before,.orb:after {{ content:""; position:absolute; inset:46px; border:1px solid rgba(255,255,255,.24); border-radius:50%; transform:rotateX(64deg); }}
.orb:after {{ transform:rotateY(62deg); }}
.dot {{ position:absolute; width:16px; height:16px; border-radius:50%; background:var(--pink); left:28%; top:35%; box-shadow:0 0 28px var(--pink); animation:float 4s infinite ease-in-out; }}
.dot:nth-child(2) {{ left:67%; top:30%; background:var(--cyan); box-shadow:0 0 28px var(--cyan); animation-delay:-1.4s; }}
.dot:nth-child(3) {{ left:52%; top:69%; background:#f9a35f; box-shadow:0 0 28px #f9a35f; animation-delay:-2.2s; }}
@keyframes float {{ 50% {{ transform:translateY(-18px) scale(1.12); }} }}
.metrics {{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin:28px 0; }}
.metric strong {{ display:block; font-size:34px; }}
.metric span {{ color:var(--muted); }}
.layout {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
section {{ margin-top:18px; }}
.bar {{ display:grid; grid-template-columns:170px 1fr 48px; gap:12px; align-items:center; margin:13px 0; color:var(--muted); }}
.bar i {{ height:14px; background:rgba(255,255,255,.11); border-radius:999px; overflow:hidden; }}
.bar b {{ display:block; height:100%; background:linear-gradient(90deg,var(--pink),var(--violet),var(--cyan)); border-radius:999px; }}
.graph {{ display:flex; flex-wrap:wrap; gap:10px; }}
.node {{ display:inline-flex; flex-direction:column; padding:10px 13px; border:1px solid var(--line); border-radius:16px; background:rgba(255,255,255,.08); }}
.node small {{ color:var(--muted); font-size:11px; margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th,td {{ text-align:left; vertical-align:top; padding:10px; border-bottom:1px solid rgba(255,255,255,.1); }}
th {{ position:sticky; top:0; background:#171023; color:white; }}
td {{ color:var(--muted); }}
.table-wrap {{ max-height:440px; overflow:auto; border:1px solid rgba(255,255,255,.1); border-radius:16px; }}
.trace {{ border-left:3px solid var(--pink); padding:11px 13px; margin:9px 0; border-radius:12px; background:rgba(255,255,255,.065); color:var(--muted); }}
pre {{ white-space:pre-wrap; color:var(--muted); line-height:1.55; }}
@media(max-width:900px) {{ .hero,.layout,.metrics {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main>
<div class="hero">
  <div>
    <h1>RevenueOps Agent Control Tower</h1>
    <p>A goal-driven agentic AI operations demo. The planner interprets an investigation goal, chooses tools, executes only those tools, stores evidence, creates action cards, routes high-risk items to human review, and records an audit trace.</p>
  </div>
  <div class="orb"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
</div>

<div class="metrics">
  <div class="panel metric"><strong>{summary['rows']}</strong><span>Accounts</span></div>
  <div class="panel metric"><strong>8800</strong><span>Opportunities</span></div>
  <div class="panel metric"><strong>{len(cards)}</strong><span>Action cards</span></div>
  <div class="panel metric"><strong>{len(review)}</strong><span>Human review</span></div>
  <div class="panel metric"><strong>{len(graph.get('edges', []))}</strong><span>Graph edges</span></div>
</div>

<section><h2>Planner Agent Output</h2>
  <p><strong>User goal:</strong> {escape(result['user_goal'])}</p>
  <p><strong>Selected tools:</strong> {escape(', '.join(result['selected_tools']))}</p>
  <p>{escape(result['agent_answer'])}</p>
</section>

<div class="layout">
  <section><h2>Investigation Modes</h2>{bars(cards)}</section>
  <section><h2>Severity Mix</h2>
    <div class="bar"><span>High</span><i><b style="width:{max(5, high)}%"></b></i><strong>{high}</strong></div>
    <div class="bar"><span>Medium</span><i><b style="width:{max(5, min(100, medium))}%"></b></i><strong>{medium}</strong></div>
    <div class="bar"><span>Low</span><i><b style="width:{max(5, low)}%"></b></i><strong>{low}</strong></div>
  </section>
</div>

<section><h2>Revenue Relationship Graph Preview</h2><div class="graph">{graph_preview(graph)}</div></section>

<section><h2>Action Card Board</h2><div class="table-wrap"><table><thead><tr>{''.join(f'<th>{c}</th>' for c in card_columns)}</tr></thead><tbody>{rows(cards, card_columns)}</tbody></table></div></section>

<section><h2>Human Review Console</h2><div class="table-wrap"><table><thead><tr>{''.join(f'<th>{c}</th>' for c in review_columns)}</tr></thead><tbody>{rows(review, review_columns)}</tbody></table></div></section>

<section><h2>Agent Trace Timeline</h2>{''.join(f"<div class='trace'>{escape(event)}</div>" for event in result['audit_trace'])}</section>

<section><h2>Investigation Report</h2><pre>{escape(report)}</pre></section>
</main>
</body>
</html>"""

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    print(render_dashboard())
