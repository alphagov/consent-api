"""CLI Command to delete expired consent statuses from the database."""
import click
from flask.cli import with_appcontext

from consent_api import app
from consent_api import models


@app.cli.command("delete-expired-consent")
@click.command()
@with_appcontext
def delete_expired_consent():
    """Delete expired consent statuses from the database."""
    models.UserConsent.bulk_delete(expired=True)
