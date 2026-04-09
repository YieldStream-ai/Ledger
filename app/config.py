from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8100
    log_level: str = "info"
    google_ai_api_key: str = ""
    llama_cloud_api_key: str = ""
    # Minimum chars of extracted text before falling to next extractor
    min_text_threshold: int = 100

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
