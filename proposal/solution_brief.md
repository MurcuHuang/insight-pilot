# Solution Brief — Self-Service AI Data Analyst

*One-page proposal template. Fill the [brackets] with your benchmark numbers and a (possibly fictional) client context. Bring this to interviews: it shows you think like a solution architect, not just a builder.*

**Client**: [mid-size e-commerce company, ~50 business staff, 4-person data team]
**Prepared by**: Yuhao | [date]

## 1. Business pain

Business teams wait [2–3 days] for ad-hoc data pulls; [60%+] of the data team's tickets are repetitive "how much / which top N / what trend" questions. Metric definitions drift between teams (e.g., whether GMV includes freight), so numbers don't reconcile in management meetings.

## 2. Proposed solution

A text-to-SQL analytics assistant grounded in a **governed semantic layer** (metrics dictionary + table semantics), with SELECT-only access to a read-only warehouse replica, automatic chart and insight generation, and per-call cost/latency observability. Architecture: see README diagram.

## 3. Model selection (benchmark-driven)

| Option | Exec. accuracy* | Hard tier | Avg latency | Cost / 1k queries | Best for |
|---|---|---|---|---|---|
| deepseek-chat | 97.5% | 94% | ~1.6s | $0.3 | **recommended default** |
| qwen3.6 @ Ollama (self-hosted) | 95% | 89% | ~12.5s | ~$0 API (GPU box: [$..]/mo) | data cannot leave premises |
| gpt-4o | 90% | 83% | ~1.8s | $3.3 | not justified: 10× cost, lower accuracy |
| glm-4-air | 85% | 78% | ~5.0s | $0.1 | budget tier for simple-query workloads |
| gpt-4o-mini | 72.5% | 67% | ~3.0s | $0.2 | not recommended for analytics SQL |

*40-question tiered benchmark (8 easy / 14 medium / 18 hard: window functions, cohort/retention, percentiles, multi-CTE) on the project warehouse, single run, temperature 0. Every failure manually attributed; raw accuracy shown (~1/3 of failures were matching artifacts, which would lift gpt-4o/glm/gpt-4o-mini by ~3–8pp).

**Recommendation**: deploy **deepseek-chat as default** — top accuracy at 1/10th the flagship's cost. On easy/medium queries all five options scored at or near 100% (and all scored 100% on the v1 12-question set), so simple-query workloads can route to the cheapest tier. Offer **self-hosted qwen3.6** as the private-deployment tier: near-leader accuracy (95%), zero data egress, trading ~6× latency. Flagship APIs are not worth the premium for this workload.

## 4. ROI estimate

[50] business users × [4] data requests/week × [30 min] analyst time saved = [100 hrs/week].
At [$40/hr] fully-loaded cost → **[$16k/month] capacity released**, vs. running cost of [$[..]/month] (LLM API at [..k] queries + hosting) → payback in [<1 month].

## 5. Implementation roadmap

POC (2 weeks: top-20 questions, 1 data mart) → Pilot (4 weeks: 1 business team, accuracy ≥ [85%] gate, feedback loop) → Rollout (SSO, row-level permissions, cost dashboards, chargeback per team).

## 6. Risks & mitigations

SQL errors → SELECT-only guard, read-only replica, self-correction loop, "show SQL" transparency, human spot-checks during pilot. Wrong-but-plausible numbers → semantic layer as single source of truth; eval set run on every prompt/model change (regression gate). Data security → private deployment option (local model), no data in prompts beyond schema + aggregates. Cost overrun → per-call logging, monthly budget alerts, caching of repeated questions.
