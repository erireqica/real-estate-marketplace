from app.config import DevelopmentConfig, ProductionConfig, TestingConfig, sqlalchemy_database_url


def test_neon_url_uses_psycopg_dialect_and_preserves_ssl_options():
    url = (
        "postgresql://user:password@example.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )

    assert sqlalchemy_database_url(url) == (
        "postgresql+psycopg://user:password@example.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )


def test_explicit_psycopg_url_is_unchanged():
    url = "postgresql+psycopg://postgres:postgres@localhost:5433/havenly"

    assert sqlalchemy_database_url(url) == url


def test_production_recycles_and_checks_connections_before_checkout():
    assert ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS == {
        "pool_pre_ping": True,
        "pool_recycle": 240,
    }


def test_neon_pool_settings_do_not_change_local_or_test_engines():
    assert not hasattr(DevelopmentConfig, "SQLALCHEMY_ENGINE_OPTIONS")
    assert not hasattr(TestingConfig, "SQLALCHEMY_ENGINE_OPTIONS")
