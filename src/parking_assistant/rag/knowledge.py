import json
from pathlib import Path

from langchain_community.vectorstores import FAISS

from parking_assistant.rag.vectorstore import get_embeddings, save_index

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "parking_knowledge.json"


def load_knowledge():
    with open(KNOWLEDGE_PATH) as f:
        return json.load(f)


def ingest():
    knowledge = load_knowledge()
    texts = [entry["content"] for entry in knowledge]
    metadatas = [{"title": entry["title"]} for entry in knowledge]

    index = FAISS.from_texts(texts, get_embeddings(), metadatas=metadatas)
    save_index(index)


if __name__ == "__main__":
    ingest()
