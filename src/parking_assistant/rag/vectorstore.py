from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings

from parking_assistant.config import settings


def get_embeddings():
    return AzureOpenAIEmbeddings(
        azure_deployment=settings.embedding_deployment,
        openai_api_key=settings.dial_api_key,
        azure_endpoint=settings.azure_endpoint,
        openai_api_version=settings.api_version,
    )


def load_index() -> FAISS:
    return FAISS.load_local(
        settings.faiss_index_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def save_index(index: FAISS) -> None:
    Path(settings.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
    index.save_local(settings.faiss_index_path)
