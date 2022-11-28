"""Flask app configuration."""
import os
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()
env = os.environ

DEBUG = env.get("DEBUG", True)

SECRET_KEY = env.get("SECRET_KEY", os.urandom(24))


def build_db_url(
    type: str = "",
    name: str = "",
    username: str = "",
    password: str = "",
    host: str = "",
    port: str | int = "",
    sock: str | None = None,
    **kwargs,
) -> str:
    """Construct a database url from parts."""
    creds = ":".join([quote(s) for s in (username, password) if s])
    addr = (f"{creds}@" if creds else "") + host + (f":{port}" if port else "")
    sock = f"?unix_sock={sock}" if sock else ""
    return f"{type}://{addr}/{name}{sock}"


SQLALCHEMY_DATABASE_URI = build_db_url(
    **{k[3:].lower(): v for k, v in env.items() if k.startswith("DB_")},
)
