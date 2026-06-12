"""Central configuration: model providers, pricing, and paths."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "warehouse.duckdb"
CHROMA_DIR = str(DATA_DIR / "chroma")
DOCS_DIR = PROJECT_ROOT / "docs"
LOG_PATH = PROJECT_ROOT / "logs" / "calls.jsonl"

# Prices are USD per 1M tokens (input, output).
# !! List prices change — verify against provider pricing pages before quoting costs.
PROVIDERS = {
    "gpt-4o-mini": dict(
        provider="openai", model="gpt-4o-mini", base_url=None,
        api_key_env="OPENAI_API_KEY", price_in=0.15, price_out=0.60),
    "claude-haiku-4-5": dict(
        provider="anthropic", model="claude-haiku-4-5", base_url=None,
        api_key_env="ANTHROPIC_API_KEY", price_in=1.00, price_out=5.00),
    "qwen-plus": dict(
        provider="openai_compatible", model="qwen-plus",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY", price_in=0.11, price_out=0.28),
    "deepseek-chat": dict(
        provider="openai_compatible", model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY", price_in=0.27, price_out=1.10),
    "glm-4-air": dict(
        provider="openai_compatible", model="glm-4-air",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key_env="ZHIPU_API_KEY", price_in=0.14, price_out=0.14),
    "gpt-4o": dict(  # optional: same-vendor tier comparison vs gpt-4o-mini
        provider="openai", model="gpt-4o", base_url=None,
        api_key_env="OPENAI_API_KEY", price_in=2.50, price_out=10.00),
    # Self-hosted option via Ollama — the "data stays on-prem" tier.
    # Set `model` to exactly what `ollama list` shows on your machine.
    "qwen3.6-local": dict(
        provider="openai_compatible", model="qwen3.6:latest",
        base_url="http://localhost:11434/v1",
        api_key_env=None, price_in=0.0, price_out=0.0,
        max_tokens=6000),  # thinking model: needs headroom for reasoning tokens
}

DEFAULT_MODEL = "gpt-4o-mini"
