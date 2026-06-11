"""Turn a result set into a chart spec + business takeaways."""
from src.llm_client import extract_json

SYSTEM = """You are a senior business analyst. Given a question and the query result, return JSON only:
{"chart": {"type": "line|bar|pie|none", "x": "<column>", "y": "<column>"},
 "insights": ["<takeaway 1>", "<takeaway 2>", "<takeaway 3>"]}

Rules:
- Chart type: time series -> line; category comparison -> bar; share/composition -> pie; single value or wide table -> none.
- "x" and "y" must be actual column names from the result.
- Insights must be specific (cite the numbers), business-oriented (so-what, not just restating), and in the same language as the question."""


def generate(question: str, sql: str, df, client) -> dict:
    preview = df.head(20).to_csv(index=False)
    user = (f"Question: {question}\n\nSQL used:\n{sql}\n\n"
            f"Result ({len(df)} rows, showing up to 20):\n{preview}")
    resp = client.chat(SYSTEM, user, stage="insights", max_tokens=600)
    try:
        return extract_json(resp.text)
    except (ValueError, Exception):
        return {"chart": {"type": "none"}, "insights": [resp.text.strip()]}


def build_figure(df, spec):
    """Chart spec -> plotly figure (or None). Defensive: bad specs just mean no chart."""
    import plotly.express as px
    chart = (spec or {}).get("chart") or {}
    ctype, x, y = chart.get("type"), chart.get("x"), chart.get("y")
    if ctype in (None, "none") or df is None or df.empty or x not in df.columns:
        return None
    if ctype == "pie":
        return px.pie(df, names=x, values=y if y in df.columns else None)
    if y not in df.columns:
        return None
    if ctype == "line":
        return px.line(df, x=x, y=y, markers=True)
    if ctype == "bar":
        return px.bar(df, x=x, y=y)
    return None
