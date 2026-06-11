"""End-to-end orchestration: route -> text-to-SQL + insights | knowledge answer | small talk."""
from src import insights, text2sql
from src.llm_client import LLMClient, extract_json
from src.semantic_layer import retrieve

ROUTER_SYSTEM = """Classify the user's message for an e-commerce analytics assistant.
Return JSON only: {"route": "data" | "knowledge" | "chat"}
- "data": needs numbers from the warehouse (totals, trends, rankings, rates, comparisons)
- "knowledge": asks about metric definitions, calculation caliber, or what a table/column means
- "chat": greetings or anything else"""

KNOWLEDGE_SYSTEM = """You are a data-governance assistant. Answer using ONLY the provided documentation, concisely, in the user's language. If the documentation doesn't cover it, say so."""

CHAT_SYSTEM = ("You are a friendly e-commerce analytics assistant. Reply in one short sentence "
               "and suggest a data question the user could ask, in the user's language.")


def answer(question: str, model_name: str) -> dict:
    client = LLMClient(model_name)
    try:
        route = extract_json(
            client.chat(ROUTER_SYSTEM, question, stage="router", max_tokens=50).text
        ).get("route", "data")
    except Exception:
        route = "data"

    if route == "data":
        result = text2sql.run(question, client)
        out = {"type": "data", **result, "chart": None, "insights": []}
        if result["df"] is not None and result["error"] is None and not result["df"].empty:
            spec = insights.generate(question, result["sql"], result["df"], client)
            out["chart"] = insights.build_figure(result["df"], spec)
            out["insights"] = spec.get("insights", [])
        return out

    if route == "knowledge":
        ctx = "\n\n".join(retrieve(question, k=4)) or "(no documentation found)"
        resp = client.chat(KNOWLEDGE_SYSTEM,
                           f"Documentation:\n{ctx}\n\nQuestion: {question}", stage="knowledge")
        return {"type": "knowledge", "text": resp.text}

    resp = client.chat(CHAT_SYSTEM, question, stage="chat", max_tokens=100)
    return {"type": "chat", "text": resp.text}
