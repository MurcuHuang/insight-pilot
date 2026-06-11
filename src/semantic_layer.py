"""Semantic layer: metric definitions + table notes from docs/, embedded in Chroma.

Build:    python -m src.semantic_layer
Retrieve: retrieve(question, k) -> list[str] of relevant doc chunks
"""
from src.config import CHROMA_DIR, DOCS_DIR

_COLLECTION = "semantic_layer"


def _get_collection():
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(_COLLECTION)


def _chunk_markdown(path):
    """Split a markdown file into chunks on '## ' headers (one chunk per metric/table)."""
    chunks, current = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") and current:
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if len(c) > 40]


def build():
    col = _get_collection()
    docs, ids = [], []
    for f in sorted(DOCS_DIR.glob("*.md")):
        for i, chunk in enumerate(_chunk_markdown(f)):
            docs.append(chunk)
            ids.append(f"{f.stem}-{i:03d}")
    col.upsert(ids=ids, documents=docs)  # idempotent: rerun after editing docs/
    print(f"Semantic layer built: {len(docs)} chunks from {DOCS_DIR}")


def retrieve(question: str, k: int = 4):
    try:
        col = _get_collection()
        if col.count() == 0:
            return []
        res = col.query(query_texts=[question], n_results=min(k, col.count()))
        return res["documents"][0]
    except Exception as e:  # degrade gracefully — SQL gen still works without context
        print(f"[semantic_layer] retrieval unavailable ({e}); continuing without context")
        return []


if __name__ == "__main__":
    build()
