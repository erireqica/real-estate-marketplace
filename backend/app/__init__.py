from flask import Flask
from .config import config_by_name
from .extensions import cors, db, jwt, migrate


def create_app(config_name: str | None = None) -> Flask:
    if config_name == "production" and not __import__("os").getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required in production.")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name or "development"])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["FRONTEND_ORIGINS"], supports_credentials=True)

    from .api import api
    from .errors import register_error_handlers
    from . import models  # noqa: F401 - registers model metadata

    app.register_blueprint(api, url_prefix="/api")
    register_error_handlers(app)
    register_commands(app)
    return app


def register_commands(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command() -> None:
        from .seed import seed_database
        seed_database()
        print("Demo data created.")
