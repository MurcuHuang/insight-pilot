# Solution Brief — Self-Service AI Data Analyst

*One-page proposal template. Fill the [brackets] with your benchmark numbers and a (possibly fictional) client context. Bring this to interviews: it shows you think like a solution architect, not just a builder.*

**Client**: [mid-size e-commerce company, ~50 business staff, 4-person data team]
**Prepared by**: Yuhao | [date]

## 1. Business pain

Business teams wait [2–3 days] for ad-hoc data pulls; [60%+] of the data team's tickets are repetitive "how much / which top N / what trend" questions. Metric definitions drift between teams (e.g., whether GMV includes freight), so numbers don't reconcile in management meetings.

## 2. Proposed solution

A text-to-SQL analytics assistant grounded in a **governed semantic layer** (metrics dictionary + table semantics), with SELECT-only access to a read-only warehouse replica, automatic chart and insight generation, and per-call cost/latency observability. Architecture: see README diagram.

## 3. Model selection (benchmark-driven)

| Option | Exec. accuracy* | Avg latency | Cost / 1k queries | Best for |
|---|---|---|---|---|
| glm-4-air | 100% | 2.8–5.3s | $0.1 | lowest cost; CN compliance |
| gpt-4o-mini | 100% | 2.3–3.4s | $0.2 | default international tier |
| deepseek-chat | 100% | ~1.8s | $0.3 | CN API, low latency |
| gpt-4o | 100% | ~1.7s | $2.8 | not justified at this task difficulty |
| qwen3.6 @ Ollama (self-hosted) | 100% | ~12.7s | ~$0 API (GPU box: [$..]/mo) | data cannot leave premises |

*12-question tiered benchmark (easy/medium/hard) on the project warehouse, single run, temperature 0. The set is saturated at current difficulty — differentiation is driven by cost, latency, and deployment form; a 40-question harder set is on the roadmap.

**Recommendation**: with semantic-layer governance + a self-correction loop, budget models match the flagship — deploy glm-4-air (CN) or gpt-4o-mini (international) as default, a **28× cost saving vs gpt-4o with no measured accuracy loss**. Offer self-hosted qwen3.6 as the private-deployment tier: zero data egress, trading ~6× latency.

## 4. ROI estimate

[50] business users × [4] data requests/week × [30 min] analyst time saved = [100 hrs/week].
At [$40/hr] fully-loaded cost → **[$16k/month] capacity released**, vs. running cost of [$[..]/month] (LLM API at [..k] queries + hosting) → payback in [<1 month].

## 5. Implementation roadmap

POC (2 weeks: top-20 questions, 1 data mart) → Pilot (4 weeks: 1 business team, accuracy ≥ [85%] gate, feedback loop) → Rollout (SSO, row-level permissions, cost dashboards, chargeback per team).

## 6. Risks & mitigations

SQL errors → SELECT-only guard, read-only replica, self-correction loop, "show SQL" transparency, human spot-checks during pilot. Wrong-but-plausible numbers → semantic layer as single source of truth; eval set run on every prompt/model change (regression gate). Data security → private deployment option (local model), no data in prompts beyond schema + aggregates. Cost overrun → per-call logging, monthly budget alerts, caching of repeated questions.
