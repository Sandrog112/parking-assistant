from parking_assistant.rag.vectorstore import load_index


def retrieve(query: str, limit: int = 3) -> list[str]:
    if not query.strip():
        return []

    index = load_index()
    docs = index.similarity_search(query, k=limit)
    return [doc.page_content for doc in docs]
