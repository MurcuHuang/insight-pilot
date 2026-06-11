"""Text-to-SQL benchmark across models: execution accuracy / latency / cost.

Usage:
    python eval/run_eval.py --models gpt-4o-mini qwen-plus deepseek-chat --lang en

Matching is approximate (value-multiset comparison per column, numerics rounded
to 2dp, column/row order ignored) — review FAIL rows manually before quoting results.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import DB_PATH, PROVIDERS          # noqa: E402
from src.llm_client import LLMClient               # noqa: E402
from src import text2sql                           # noqa: E402


def signature(df):
    """Order-insensitive signature of a result set for approximate matching."""
    if df is None:
        return None
    cols = []
    for c in df.columns:
        col = df[c]
        try:
            if pd.api.types.is_numeric_dtype(col):
                col = col.astype(float).round(2)
        except Exception:
            pass
        cols.append(tuple(sorted(str(v) for v in col.tolist())))
    return tuple(sorted(cols))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["gpt-4o-mini"], choices=list(PROVIDERS))
    ap.add_argument("--lang", choices=["en", "zh"], default="en")
    ap.add_argument("--tiers", nargs="+", default=["easy", "medium", "hard"])
    args = ap.parse_args()

    questions = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    questions = [q for q in questions if q["tier"] in args.tiers]

    con = duckdb.connect(str(DB_PATH), read_only=True)
    gold = {q["id"]: signature(con.execute(q["gold_sql"]).fetchdf()) for q in questions}
    con.close()

    rows = []
    for name in args.models:
        client = LLMClient(name)
        for q in questions:
            text = q["question"] if args.lang == "en" else q["question_zh"]
            r = text2sql.run(text, client)
            ok = (r["error"] is None and r["df"] is not None
                  and signature(r["df"]) == gold[q["id"]])
            rows.append({"model": name, "id": q["id"], "tier": q["tier"], "correct": ok,
                         "attempts": r["attempts"], "latency_s": r["latency_s"],
                         "cost_usd": r["cost_usd"], "error": (r["error"] or "")[:120],
                         "sql": r["sql"]})
            print(f"[{name}] {q['id']:>3} {'PASS' if ok else 'FAIL'}"
                  f"  ({r['latency_s']}s, ${r['cost_usd']:.5f}, {r['attempts']} attempt(s))")

    res = pd.DataFrame(rows)
    out = ROOT / "eval" / "results"
    out.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    res.to_csv(out / f"results_{ts}.csv", index=False)

    summary = res.groupby("model").agg(
        accuracy=("correct", "mean"),
        avg_latency_s=("latency_s", "mean"),
        avg_cost_usd=("cost_usd", "mean"),
        total_cost_usd=("cost_usd", "sum"),
    ).round(4)
    summary["cost_per_1k_queries_usd"] = (summary["avg_cost_usd"] * 1000).round(2)
    by_tier = res.pivot_table(index="model", columns="tier", values="correct",
                              aggfunc="mean").round(3)

    print("\n=== Summary ===")
    print(summary.to_string())
    print("\n=== Accuracy by tier ===")
    print(by_tier.to_string())
    (out / f"summary_{ts}.md").write_text(
        summary.to_markdown() + "\n\n" + by_tier.to_markdown(), encoding="utf-8")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
