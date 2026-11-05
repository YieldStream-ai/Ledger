from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8100
    log_level: str = "info"
    google_ai_api_key: str = ""
    llama_cloud_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    # Minimum chars of extracted text before falling to next extractor
    min_text_threshold: int = 100

    # Async job pipeline (S3 → SQS → worker Lambda, job state in DynamoDB)
    aws_region: str = "us-west-2"
    jobs_bucket: str = ""
    jobs_table: str = ""
    max_upload_mb: int = 20

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
