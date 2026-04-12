from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from parking_assistant.config import settings


def get_embeddings():
    return OpenAIEmbeddings(api_key=settings.openai_api_key)


def load_index() -> FAISS:
    return FAISS.load_local(
        settings.faiss_index_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def save_index(index: FAISS) -> None:
    Path(settings.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
    index.save_local(settings.faiss_index_path)
