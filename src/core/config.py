from datetime import timedelta
from pathlib import Path
from typing import Literal

from authx.types import AlgorithmType, TokenLocation, SameSitePolicy
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    mode: Literal["DEV", "TEST", "PROD"] = "DEV"
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"


class ApiConfig(BaseModel):
    title: str = "Micro-reddit"
    version: str = "0.5-dev"


class FilesConfig(BaseModel):
    # Базовые пути
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    src_dir: Path = base_dir / "src"

    # Переменные окружения
    env_file: Path = base_dir / ".env"
    env_example_file: Path = base_dir / ".env.example"

    # Логирование
    logs_dir: Path = base_dir / "logs"
    logs_file: Path = logs_dir / "app.log"

    # Миграции
    alembic_dir: Path = base_dir / "migrations"
    alembic_ini: Path = base_dir / "alembic.ini"


class LogsConfig(BaseModel):
    level: Literal["DEBUG", "INFO"] = "INFO"
    format: str = "[%(asctime)s] - %(name)-26s - %(levelname)-7s - %(message)s"


class DatabaseConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int
    name: str

    echo: int = 0

    @property
    def POSTGRES_DSN(self):
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class JWTConfig(BaseModel):
    # Общая настройка
    algorithm: AlgorithmType
    secret_key: str

    # Токен доступа
    access_location: TokenLocation = "headers"
    access_expires: timedelta = timedelta(minutes=30)

    # Токен обновления
    refresh_location: TokenLocation = "cookies"
    refresh_expires: timedelta = timedelta(days=14)

    # Куки
    cookie_http_only: bool = True
    cookie_secure: bool = True
    cookie_max_age: int = int(refresh_expires.total_seconds())
    cookie_samesite: SameSitePolicy = "lax"
    cookie_session: bool = False


class BrokerConfig(BaseModel):
    username: str
    password: str
    host: str
    port: str

    @property
    def AMQP_DSN(self):
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/"


class Settings(BaseSettings):
    api: ApiConfig = ApiConfig()
    run: RunConfig = RunConfig()
    files: FilesConfig = FilesConfig()
    log: LogsConfig = LogsConfig()

    db: DatabaseConfig
    broker: BrokerConfig
    jwt: JWTConfig

    model_config = SettingsConfigDict(
        env_file=(files.env_example_file, files.env_file),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
    )


settings = Settings()
