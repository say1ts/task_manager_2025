from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс для управления конфигурацией приложения.
    Загружает переменные из .env файла.
    """

    DATABASE_URL: str
    ECHO_SQL: bool = False

    AUTH_SECRET_KEY: str
    AUTH_ALGORITHM: str = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
