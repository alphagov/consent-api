import base64
import uuid


def generate_uid():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf8").rstrip("=")
