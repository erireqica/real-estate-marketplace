import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def sqlalchemy_database_url(value: str) -> str:
    """Select the installed psycopg 3 dialect without altering URL options."""
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-jwt-secret-change-before-deploy-32-chars")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    FRONTEND_ORIGINS = [origin.strip() for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",") if origin.strip()]
    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = sqlalchemy_database_url(os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5433/havenly"
    ))


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = False


class ProductionConfig(BaseConfig):
    # Hosting platforms inject this value at runtime. Keeping import side effects
    # out of configuration allows tooling and tests to load the app safely.
    SQLALCHEMY_DATABASE_URI = sqlalchemy_database_url(os.getenv("DATABASE_URL", ""))
    # Neon can terminate idle connections when its compute scales to zero.
    # Validate connections at checkout and retire them before the usual
    # five-minute suspension window can leave stale handles in a web worker.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 240,
    }


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
