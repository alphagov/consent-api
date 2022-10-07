import base64
import uuid
from urllib.parse import parse_qs, urlparse


def generate_uid():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf8").rstrip("=")


def get_uid_from_referrer(referrer: str) -> str | None:
    return parse_qs(urlparse(referrer).query).get("uid", [None])[0]
