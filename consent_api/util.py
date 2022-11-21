"""Utility functions."""
import base64
import uuid


def generate_uid():
    """
    Generate a random 22 character identifier string.

    This is an encoded UUID4, so should have no personally identifying information.
    """
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf8").rstrip("=")
