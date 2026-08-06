from app.config import sqlalchemy_database_url


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
