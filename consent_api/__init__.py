from flask import Flask


app = Flask(__name__)

import consent_api.views
