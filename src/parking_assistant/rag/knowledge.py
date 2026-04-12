import json
from pathlib import Path

import weaviate.classes.config as wc

from parking_assistant.rag.vectorstore import get_client

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "parking_knowledge.json"


def load_knowledge():
    with open(KNOWLEDGE_PATH) as f:
        return json.load(f)


def ingest():
    client = get_client()
    try:
        if client.collections.exists("ParkingKnowledge"):
            client.collections.delete("ParkingKnowledge")

        client.collections.create(
            name="ParkingKnowledge",
            vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(),
            generative_config=wc.Configure.Generative.openai(),
            properties=[
                wc.Property(name="title", data_type=wc.DataType.TEXT),
                wc.Property(name="content", data_type=wc.DataType.TEXT),
            ],
        )

        collection = client.collections.get("ParkingKnowledge")
        knowledge = load_knowledge()

        with collection.batch.dynamic() as batch:
            for entry in knowledge:
                batch.add_object(properties={"title": entry["title"], "content": entry["content"]})
    finally:
        client.close()


if __name__ == "__main__":
    ingest()
