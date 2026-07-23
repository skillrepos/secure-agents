"""
Lab 2 - Build the vector database (provided complete).

Indexes every document in docs/ into a local Chroma vector DB with real
embeddings. This simulates an attacker who has slipped a poisoned document
into the knowledge base: the legitimate handbook/returns docs AND the
poisoned bulletin are embedded into the SAME collection, with metadata that
makes the poisoned chunks look like they came from a real PDF.

Run this once before rag_vulnerable.py / rag_hardened.py.
"""
import chromadb
import kb

POISONED = "OmniTech_Security_Bulletin_2024.pdf"


def main():
    client = chromadb.PersistentClient(path=kb.DB_DIR)
    # Rebuild from scratch each run so the lab is reproducible.
    try:
        client.delete_collection(kb.COLLECTION)
    except Exception:
        pass
    col = client.create_collection(kb.COLLECTION, metadata={"hnsw:space": "cosine"})

    chunks = kb.load_chunks_from_docs()
    col.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"]} for c in chunks],
        ids=[f"chunk-{i}" for i in range(len(chunks))],
    )

    print(f"=== Built Chroma collection '{kb.COLLECTION}' at {kb.DB_DIR} ===")
    print(f"Indexed {len(chunks)} chunks (real embeddings).\n")
    by_source = {}
    for c in chunks:
        by_source[c["source"]] = by_source.get(c["source"], 0) + 1
    for src, n in sorted(by_source.items()):
        flag = "  <-- POISONED (injected by attacker)" if src == POISONED else ""
        print(f"  {n:>2} chunks  {src}{flag}")
    print("\nThe poisoned chunks now sit in the same vector store as the real "
          "ones, retrieved by semantic similarity like any other content.")


if __name__ == "__main__":
    main()
