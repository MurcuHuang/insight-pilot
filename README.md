# InsightPilot — LLM-Powered AI Data Analyst

Ask a business question in plain English (or Chinese) over an e-commerce data warehouse and get **validated SQL, charts, and business takeaways** — plus the two things a real enterprise rollout needs:

1. **Model selection benchmark** — execution accuracy / latency / cost compared across GPT, Claude, Qwen, DeepSeek, and a self-hosted local model, so "which model should we use?" is answered with data, not vibes.
2. **Ops cost monitor** — every LLM call is logged (tokens, latency, cost) and visualized, so you know what this costs at scale before a client asks.

> Built as a solution-architecture portfolio project: the deliverable is not just a demo, but a defensible answer to *"which model/deployment should we choose, and what will it cost per 1,000 queries?"*

## The business problem

Business teams wait days for ad-hoc data pulls; data teams drown in repetitive "how much / how many / which top 5" requests. A text-to-SQL assistant grounded in a **governed semantic layer** (metric definitions, calculation caliber) lets business users self-serve while keeping numbers consistent.

## Architecture

```
User question (natural language)
   │
   ▼
Router (LLM) ──► metric/definition question ──► Semantic layer (Chroma RAG over
   │                                            metrics dictionary + table notes)
   ▼ data question
Text-to-SQL (LLM + live schema + retrieved metric definitions)
   │   ◄── self-correction loop: execution errors / empty results
   │        fed back to the model (max 2 retries, SELECT-only guard)
   ▼
DuckDB warehouse (Olist-style e-commerce, 7 tables, ~18k orders)
   │
   ▼
Insight layer (LLM) ──► Plotly chart spec + 3 business takeaways
   │
   ▼
Streamlit UI ──┬── 💬 Chat: SQL + table + chart + insights
               └── 🖥️ Ops monitor: tokens / latency / cost per call & per model
```

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in the API keys you have (any subset works)

python scripts/generate_synthetic_data.py   # or drop real Kaggle Olist CSVs into data/raw/
python scripts/build_db.py                  # CSVs -> DuckDB warehouse
python -m src.semantic_layer                # build the RAG semantic layer

streamlit run app.py
```

Try: *"Monthly GMV trend in 2025"*, *"Top 5 categories by revenue"*, *"复购率是多少?"*, *"Do late deliveries hurt review scores?"*, *"How is GMV defined?"*

## Run the model benchmark

```bash
python eval/run_eval.py --models gpt-4o-mini qwen-plus deepseek-chat --lang en
```

Outputs per-model **execution accuracy (by difficulty tier), avg latency, cost per query, and estimated cost per 1k queries** to `eval/results/`. Add a local model via Ollama (`ollama run qwen2.5:7b`) to benchmark the "self-hosted / data-stays-onsite" option.

Result matching is approximate (value-multiset comparison, numerics rounded to 2dp) — manually review FAIL rows before quoting numbers.

### Benchmark results (v2: 40-question set — 8 easy / 14 medium / 18 hard)

The v2 set adds window functions, cohort/retention analysis, percentiles, and multi-CTE composites. Every FAIL was manually attributed: of 24 failures, ~16 were genuine model errors and ~8 were matching artifacts / question ambiguities (e.g., timestamp vs integer year, percentile interpolation method).

| Model | Raw accuracy | Adj. accuracy* | Hard tier | Avg latency | Cost / 1k queries |
|---|---|---|---|---|---|
| deepseek-chat | 97.5% | 97.5% | 94% | ~1.6s | $0.3 |
| qwen3.6 @ Ollama (self-hosted) | 95% | 95% | 89% | ~12.5s | ~$0 API |
| gpt-4o | 90% | ~93% | 83% | ~1.8s | $3.3 |
| glm-4-air | 85% | ~90% | 78% | ~5.0s | $0.1 |
| gpt-4o-mini | 72.5% | ~80% | 67% | ~3.0s | $0.2 |

*Adjusted = excluding fails attributed to matching artifacts rather than model errors.

**Takeaways**: (1) On the saturated v1 12-question set, all five options scored 100% — system design (semantic layer + self-correction) matters more than model choice for routine queries. (2) The harder v2 set separates them: the flagship gpt-4o is beaten by deepseek-chat at 1/10th the cost, and the self-hosted model nearly matches the API leader — privacy costs ~6× latency, not accuracy. (3) Recurring genuine failure modes: `date_diff` argument-order reversal (caught both OpenAI models — negative durations silently bucketed wrong), multi-step aggregation grain errors, and reasoning-token exhaustion on a local thinking model. (4) Semantic-layer governance demonstrably lifts weak models: seeding a reference SQL template took glm-4-air on repeat-purchase-rate from 3 failed attempts to first-pass correct.

## Data

Synthetic Olist-style dataset generated with built-in, realistic signals:

- Nov/Dec seasonality + 25% YoY growth
- ~13% late deliveries, and late delivery **strongly lowers review scores** (so causal-flavored questions have real answers)
- `customer_id` is per-order; `customer_unique_id` identifies the person — the classic repeat-purchase-rate trap, documented in the semantic layer

To use the real [Kaggle Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) instead, see `data/README.md`.

## Project structure

```
├── app.py                      # Streamlit UI (chat + ops monitor)
├── src/
│   ├── config.py               # providers, pricing (USD/1M tokens), paths
│   ├── llm_client.py           # unified OpenAI/Anthropic/compatible client + cost tracking
│   ├── semantic_layer.py       # Chroma RAG over docs/ (build + retrieve)
│   ├── text2sql.py             # schema-grounded SQL gen + self-correction loop
│   ├── insights.py             # chart spec + business takeaways
│   ├── pipeline.py             # router + orchestration
│   └── logger.py               # JSONL call log (tokens/latency/cost)
├── scripts/                    # synthetic data generator, DB builder
├── docs/                       # metrics dictionary + table notes (the semantic layer)
├── eval/                       # tiered question set + benchmark runner
└── proposal/                   # one-page client solution brief
```

## Roadmap

- Multi-run evaluation with variance analysis; questions that should be refused or clarified
- Query result caching + few-shot retrieval from past correct SQL
- Docker compose (app + Ollama) for one-command private deployment
- Row-level access control on the warehouse

## Notes

- Prices in `src/config.py` are **per-1M-token list prices — verify against current provider pricing pages** before quoting costs.
- The generated SQL is restricted to SELECT and runs on a read-only connection.
