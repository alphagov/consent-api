"""Set up Jinja2 templates."""


import jinja2
from starlette.templating import Jinja2Templates

from consent_api.config import CONSENT_API_ORIGIN

templates = Jinja2Templates(
    directory="consent_api/templates",  # required but overridden by loader arg
    loader=jinja2.ChoiceLoader(
        [
            jinja2.FileSystemLoader("consent_api/templates"),
            jinja2.PrefixLoader(
                {"govuk_frontend_jinja": jinja2.PackageLoader("govuk_frontend_jinja")}
            ),
        ],
    ),
)
templates.env.globals.update(
    {"CONSENT_API_BASE_URL": CONSENT_API_ORIGIN},
)
