"""JSONL call logger + reader. Every LLM call lands here; the ops monitor reads it."""
import json
import time

import pandas as pd

from src.config import LOG_PATH


def log_call(model, stage, input_tokens, output_tokens, latency_s, cost_usd, success=True):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model, "stage": stage,
        "input_tokens": int(input_tokens), "output_tokens": int(output_tokens),
        "latency_s": round(latency_s, 3), "cost_usd": round(cost_usd, 6),
        "success": bool(success),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def read_log() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame()
    return pd.read_json(LOG_PATH, lines=True)
