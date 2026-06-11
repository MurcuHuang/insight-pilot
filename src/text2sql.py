"""Text-to-SQL with live schema grounding, semantic-layer context,
a SELECT-only guard, and a self-correction loop (errors / empty results fed back)."""
import re

import duckdb

from src.config import DB_PATH
from src.semantic_layer import retrieve

SYSTEM = """You are a senior analytics engineer. Write a single DuckDB SQL query that answers the user's question.

Rules:
- Output exactly one SQL query inside a ```sql code block. No explanations.
- SELECT-only. Never modify data.
- Use only the tables/columns in the provided schema.
- When a metric is defined in the business definitions, follow that definition EXACTLY (filters, join keys, included/excluded fields).
- Use clear column aliases; round monetary values to 2 decimals.
- Add ORDER BY where it aids readability; add LIMIT 100 for row-level (non-aggregated) outputs.
- DuckDB date functions: date_trunc('month', ts), date_diff('day', start_ts, end_ts), ts >= '2025-01-01'."""

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|copy|pragma|install|load)\b", re.I)


def get_schema(con) -> str:
    rows = con.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'main' ORDER BY table_name, ordinal_position").fetchall()
    tables = {}
    for t, c, d in rows:
        tables.setdefault(t, []).append(f"{c} {d}")
    return "\n".join(f"{t}({', '.join(cols)})" for t, cols in tables.items())


def extract_sql(text: str) -> str:
    m = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return (m.group(1) if m else text).strip()


def run(question: str, client, max_retries: int = 2) -> dict:
    """Returns {sql, df, error, attempts, latency_s, cost_usd}."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    schema = get_schema(con)
    context = "\n\n".join(retrieve(question))
    base = (f"### Warehouse schema (DuckDB)\n{schema}\n\n"
            f"### Business definitions (follow these exactly)\n{context or '(none)'}\n\n"
            f"### Question\n{question}")

    sql, df, error, feedback = None, None, None, ""
    attempts, total_cost, total_latency = 0, 0.0, 0.0
    retried_empty = False

    while attempts <= max_retries:
        attempts += 1
        resp = client.chat(SYSTEM, base + feedback, stage="text2sql",
                           max_tokens=client.cfg.get("max_tokens", 1500))
        total_cost += resp.cost_usd
        total_latency += resp.latency_s
        sql = extract_sql(resp.text)

        if not sql.strip():  # e.g. thinking models exhausting max_tokens before any output
            error = "Model returned no SQL (empty response — possibly max_tokens exhausted by reasoning)."
            feedback = "\n\n### Previous attempt returned NOTHING. Output only the final ```sql block, no reasoning."
            continue
        if _FORBIDDEN.search(sql):
            error = "Generated SQL contained a write/DDL operation and was blocked."
            feedback = (f"\n\n### Previous attempt (REJECTED — not SELECT-only)\n```sql\n{sql}\n```\n"
                        "Only SELECT queries are allowed. Return a corrected ```sql block.")
            continue
        try:
            df = con.execute(sql).fetchdf()
            error = None
        except Exception as e:
            error, df = str(e), None
            feedback = (f"\n\n### Previous attempt (FAILED)\n```sql\n{sql}\n```\n"
                        f"DuckDB error: {error}\nFix the query and return a corrected ```sql block.")
            continue
        if df.empty and not retried_empty:
            retried_empty = True
            feedback = (f"\n\n### Previous attempt (retur