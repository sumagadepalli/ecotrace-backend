from pathlib import Path

from dotenv import dotenv_values
from flask_sqlalchemy import SQLAlchemy


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

config = dotenv_values(ENV_FILE)

db = SQLAlchemy()


def init_db(app):
    database_url = config.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            f"DATABASE_URL is not configured. Checked: {ENV_FILE}"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)