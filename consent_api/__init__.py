"""Consent API Flask app."""
from dataclasses import dataclass

from flask import Flask
from flask import render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


@dataclass
class ErrorPageHandler:
    """Renders an error page."""

    code: int
    template: str

    def __call__(self, _) -> tuple[str, int]:
        """Render an error page for the specified error code."""
        return render_template(self.template, code=self.code), self.code


app = Flask(__name__)
app.config.from_object("consent_api.config")

# assign error page handlers to all error status codes we care about
for template, codes in {
    "errors/404.html": [404],
    "errors/4xx.html": [401, 405, 406, 408, 409],
    "errors/503.html": [503],
    "errors/5xx.html": [500, 501, 502, 504, 505],
}.items():
    for code in codes:
        app.register_error_handler(code, ErrorPageHandler(code, template))

db = SQLAlchemy()
db.init_app(app)

migrate = Migrate()
migrate.init_app(app, db)

import consent_api.commands  # noqa
import consent_api.views  # noqa
