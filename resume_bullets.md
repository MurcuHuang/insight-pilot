# 简历项目描述(中英文)

> 用法:项目名 + 3-4 条 bullet。投 SA/售前岗用完整版;空间不够删掉第 4 条。
> 数字均来自你自己跑出的评测结果,面试可深挖,放心写。

---

## English (for AWS / international roles)

**InsightPilot — LLM-Powered Self-Service Data Analyst** | Python, DuckDB, RAG (Chroma), Streamlit | [GitHub link]

- Built an end-to-end AI data analyst over a 7-table e-commerce warehouse: LLM intent routing, a RAG semantic layer enforcing governed metric definitions, text-to-SQL with a SELECT-only guard and execution-feedback self-correction loop, and automatic chart + insight generation.
- Designed a tiered text-to-SQL benchmark (execution accuracy / latency / cost) across 5 deployment options (GPT-4o, GPT-4o-mini, DeepSeek, GLM, self-hosted Qwen via Ollama); diagnosed and eliminated false-negative result matching, bringing all models to 100% on the question set and exposing a 28× cost spread ($0.1–$2.8 per 1k queries) with no accuracy difference.
- Demonstrated semantic-layer governance ROI: seeding a reference SQL template for a commonly mis-calibrated metric (repeat purchase rate) lifted a budget model from 3 failed attempts to first-pass correct — enabling low-cost model deployment at scale.
- Instrumented per-call observability (tokens, latency, cost) with an ops dashboard, and authored a one-page client solution brief covering model selection, ROI estimate, rollout plan, and risk mitigations.

## 中文(国内云厂商 / 大厂 / AI 初创)

**InsightPilot — 企业级 AI 数据分析助手(LLM + 语义层治理)** | Python, DuckDB, RAG (Chroma), Streamlit | [GitHub 链接]

- 基于 7 表电商数仓搭建端到端 AI 取数助手:LLM 意图路由 + RAG 语义层(统一指标口径)+ Text-to-SQL(只读防护、执行报错回喂的自我修正循环)+ 自动图表与业务洞察生成。
- 设计分层 Text-to-SQL 评测(执行准确率/延迟/成本),横向对比 5 种部署方案(GPT-4o、GPT-4o-mini、DeepSeek、GLM、Ollama 本地 Qwen);定位并修复评测假阴性后,全部模型达到 100% 准确率,揭示 28 倍成本价差下无准确率差异,支撑"便宜模型 + 系统治理"的选型结论。
- 验证语义层治理价值:将易错口径(复购率)的参考 SQL 沉淀进指标字典,使低价模型从 3 次尝试全败提升为一次通过,显著降低规模化部署成本。
- 实现全链路可观测(逐调用 token/延迟/成本看板),并产出一页纸客户方案书(选型对比、ROI 测算、实施路径、风险对策)。

---

## 面试常见追问(提前准备)

- 自我修正循环怎么实现?→ 执行 SQL,把 DuckDB 报错原文 + 上次 SQL 拼回 prompt 重试,最多 2 次;空结果单独重试一次;正则禁写操作 + 只读连接双保险。
- 为什么所有模型都 100%,你的评测是不是太简单?→ 是,12 题在治理良好的语义层下已饱和——这恰恰是结论(系统设计 > 模型选择);roadmap 是扩 40 道更难的题(窗口函数、留存分析、应拒答的模糊问题)拉开区分度。
- 复购率那题为什么容易错?→ customer_id 是订单粒度,人是 customer_unique_id,模型默认口径会算错;靠指标字典 + 参考 SQL 解决,这是数据治理问题不是模型问题。
- 成本数字怎么来的?→ 每次调用按 token 用量 × 牌价记账(JSONL 日志),监控页可视化;牌价写在配置里,引用前会核对官网。
- 局限?→ 合成数据(真实 Olist 可一键替换)、单次运行、12 题样本小、值匹配是近似比较。
