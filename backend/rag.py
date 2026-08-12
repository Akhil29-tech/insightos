import os
import re
import chromadb
from chromadb.utils import embedding_functions

KB_DIR = "knowledge_base"
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "insightos_knowledge"

def load_sections(filepath, source_label):
    """Split a markdown file into chunks by ## headers."""
    with open(filepath, "r") as f:
        content = f.read()
    sections = re.split(r"\n(?=## )", content)
    docs = []
    for section in sections:
        section = section.strip()
        if not section or section.startswith("# "):
            continue
        title_match = re.match(r"## (.+)", section)
        title = title_match.group(1) if title_match else "untitled"
        docs.append({
            "id": f"{source_label}::{title}",
            "text": section,
            "title": title,
            "source": source_label,
        })
    return docs

def build_knowledge_base():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Fresh rebuild each time this script runs
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedder,
    )

    docs = []
    docs += load_sections(f"{KB_DIR}/metric_definitions.md", "metric_definition")
    docs += load_sections(f"{KB_DIR}/schema_docs.md", "schema_doc")

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[{"title": d["title"], "source": d["source"]} for d in docs],
    )

    print(f"Indexed {len(docs)} knowledge base sections into Chroma.")
    return collection

def retrieve(query, n_results=4):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_collection(COLLECTION_NAME, embedding_function=embedder)
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0]

if __name__ == "__main__":
    build_knowledge_base()
    print("\n--- Test retrieval ---")
    test_query = "which region had the most late deliveries"
    results = retrieve(test_query)
    for r in results:
        print("\n" + r[:150] + "...")
