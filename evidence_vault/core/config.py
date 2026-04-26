from pydantic import BaseSettings

class Settings(BaseSettings):
    db_path: str = "evidence.db"
    fernet_key: str = None

    class Config:
        env_file = ".env"

settings = Settings()