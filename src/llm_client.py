"""Unified LLM client across OpenAI / Anthropic / OpenAI-compatible providers,
with per-call latency + cost tracking (logged via src.logger)."""
import json
import os
import re
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from src.config import PROVIDERS
from src.logger import log_call

load_dotenv()


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float


class LLMClient:
    def __init__(self, name: str):
        if name not in PROVIDERS:
            raise KeyError(f"Unknown model '{name}'. Options: {list(PROVIDERS)}")
        self.name = name
        self.cfg = PROVIDERS[name]
        key_env = self.cfg["api_key_env"]
        key = os.getenv(key_env) if key_env else "local"
        if not key:
            raise EnvironmentError(f"Set {key_env} in .env to use '{name}'")
        if self.cfg["provider"] == "anthropic":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=key)
        else:
            from openai import OpenAI
            self._client = OpenAI(api_key=key, base_url=self.cfg.get("base_url"))

    def chat(self, system: str, user: str, temperature: float = 0.0,
             max_tokens: int = 1500, stage: str = "generic") -> LLMResponse:
        t0 = time.time()
        try:
            if self.cfg["provider"] == "anthropic":
                resp = self._client.messages.create(
                    model=self.cfg["model"], system=system, max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": user}])
                text = resp.content[0].text
                tin, tout = resp.usage.input_tokens, resp.usage.output_tokens
            else:
                resp = self._client.chat.completions.create(
                    model=self.cfg["model"], temperature=temperature, max_tokens=max_tokens,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}])
                text = resp.choices[0].message.content or ""
                tin = getattr(resp.usage, "prompt_tokens", 0) or 0
                tout = getattr(resp.usage, "completion_tokens", 0) or 0
        except Exception:
            log_call(self.name, stage, 0, 0, time.time() - t0, 0.0, success=False)
            raise
        latency = time.time() - t0
        cost = (tin * self.cfg["price_in"] + tout * self.cfg["price_out"]) / 1e6
        log_call(self.name, stage, tin, tout, latency, cost)
        return LLMResponse(text, tin, tout, latency, cost)


def extract_json(text: str) -> dict:
    """Parse a JSON object from an LLM reply (tolerates ``` fences and prose)."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON object found in: {text[:200]}")
    return json.loads(m.group(0))
