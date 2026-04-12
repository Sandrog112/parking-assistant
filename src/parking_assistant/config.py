from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    faiss_index_path: str = "data/faiss_index"
    reservations_file: str = "data/reservations.json"
    llm_model: str = "gpt-4o-mini"
    mcp_server_url: str = "http://localhost:8000"


settings = Settings()
