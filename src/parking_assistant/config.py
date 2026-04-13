from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    dial_api_key: str = ""
    azure_endpoint: str = "https://ai-proxy.lab.epam.com"
    api_version: str = "2024-02-01"
    azure_deployment: str = "gpt-4o-mini"
    embedding_deployment: str = "text-embedding-ada-002"
    faiss_index_path: str = "data/faiss_index"
    reservations_file: str = "data/reservations.json"
    mcp_server_url: str = "http://localhost:8000"


settings = Settings()
