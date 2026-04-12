from parking_assistant.rag.vectorstore import get_client, get_collection


def retrieve(query: str, limit: int = 3) -> list[str]:
    if not query.strip():
        return []

    client = get_client()
    try:
        collection = get_collection(client)
        response = collection.query.near_text(query=query, limit=limit)
        return [obj.properties["content"] for obj in response.objects]
    finally:
        client.close()
