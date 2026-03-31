from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "智能值班闭环 Demo 系统"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite+pysqlite:///:memory:"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
