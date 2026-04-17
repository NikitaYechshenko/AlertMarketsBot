from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    # Database
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    CHAT_ID: int

    # Workers optimization
    ALERTS_NO_ALERTS_TTL_SECONDS: float = 1.5
    ALERTS_MAX_CONCURRENT_CHECKS: int = 200

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
