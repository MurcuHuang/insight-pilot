"""List the models each configured API key can access, and verify the
model names in src/config.py actually exist.

Usage: python scripts/check_models.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os

from dotenv import load_dotenv
from openai import OpenAI

from src.config import PROVIDERS

load_dotenv()

ENDPOINTS = {  # provider label -> (env var, base_url)
    "OpenAI": ("OPENAI_API_KEY", None),
    "DeepSeek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com"),
    "Zhipu GLM": ("ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4"),
    "Ollama (local)": (None, "http://localhost:11434/v1"),
}

configured = {cfg["model"] for cfg in PROVIDERS.values()}

for label, (env, base_url) in ENDPOINTS.items():
    key = os.getenv(env) if env else "local"
    if not key:
        print(f"\n## {label}: skipped (no {env} in .env)")
        continue
    print(f"\n## {label}")
    try:
        client = OpenAI(api_key=key, base_url=base_url)
        models = sorted(m.id for m in client.models.list())
        for m in models:
            mark = "  <-- used in src/config.py" if m in configured else ""
            print(f"  {m}{mark}")
    except Exception as e:
        print(f"  could not list models ({str(e)[:100]})")
        print("  -> check the key, or look up available models in the provider's console/docs")
