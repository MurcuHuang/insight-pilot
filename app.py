"""InsightPilot — Streamlit UI: chat analytics + ops monitor."""
import streamlit as st

from src.config import DEFAULT_MODEL, PROVIDERS
from src.logger import read_log

st.set_page_config(page_title="InsightPilot — AI Data Analyst", layout="wide")
st.title("📊 InsightPilot — AI Data Analyst")

model = st.sidebar.selectbox("Model", list(PROVIDERS),
                             index=list(PROVIDERS).index(DEFAULT_MODEL))
st.sidebar.caption("Switch models to compare quality / latency / cost — see the Ops monitor tab.")
st.sidebar.markdown("**Try asking:**")
for ex in ["Monthly GMV trend in 2025", "Top 5 categories by revenue",
           "Do late deliveries hurt review scores?", "复购率是多少?", "How is GMV defined?"]:
    st.sidebar.markdown(f"- *{ex}*")

tab_chat, tab_ops = st.tabs(["💬 Ask the data", "🖥️ Ops monitor"])

# ---------------- chat ----------------
with tab_chat:
    if "history" not in st.session_state:
        st.session_state.history = []

    for q, res in st.session_state.history:
        st.chat_message("user").write(q)
        with st.chat_message("assistant"):
            if res["type"] == "data":
                if res.get("error"):
                    st.error(f"Query failed after {res['attempts']} attempt(s): {res['error']}")
                    if res.get("sql"):
                        st.code(res["sql"], language="sql")
                else:
                    with st.expander("Generated SQL", expanded=False):
                        st.code(res["sql"], language="sql")
                    if res["df"] is not None:
                        st.dataframe(res["df"].head(100), use_container_width=True)
                    if res.get("chart") is not None:
                        st.plotly_chart(res["chart"], use_container_width=True)
                    for tip in res.get("insights", []):
                        st.markdown(f"- {tip}")
                    st.caption(f"{res['attempts']} attempt(s) · {res['latency_s']}s · "
                               f"${res['cost_usd']:.5f} ({res.get('model', '')})")
            else:
                st.write(res["text"])

    question = st.chat_input("Ask a business question, e.g. 'Monthly GMV trend in 2025'")
    if question:
        from src.pipeline import answer  # lazy import: keeps app startup fast
        with st.spinner(f"Analyzing with {model}..."):
            try:
                res = answer(question, model)
                res["model"] = model
            except Exception as e:
                res = {"type": "chat", "text": f"⚠️ {e}"}
        st.session_state.history.append((question, res))
        st.rerun()

# ---------------- ops monitor ----------------
with tab_ops:
    df = read_log()
    if df.empty:
        st.info("No LLM calls logged yet — ask a question first.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total calls", f"{len(df):,}")
        c2.metric("Total cost", f"${df['cost_usd'].sum():.4f}")
        c3.metric("Avg latency", f"{df['latency_s'].mean():.2f}s")
        c4.metric("Success rate", f"{df['success'].mean():.1%}")

        import plotly.express as px
        left, right = st.columns(2)
        with left:
            st.subheader("Cost by model")
            agg = df.groupby("model", as_index=False)["cost_usd"].sum()
            st.plotly_chart(px.bar(agg, x="model", y="cost_usd"), use_container_width=True)
        with right:
            st.subheader("Avg latency by stage")
            agg = df.groupby(["model", "stage"], as_index=False)["latency_s"].mean()
            st.plotly_chart(px.bar(agg, x="stage", y="latency_s", color="model",
                                   barmode="group"), use_container_width=True)

        st.subheader("Recent calls")
        st.dataframe(df.tail(50).iloc[::-1], use_container_width=True)
