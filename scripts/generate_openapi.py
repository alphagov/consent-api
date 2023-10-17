# flake8: noqa: E402

import sys

sys.path.append("..")

import json

from consent_api import app

if __name__ == "__main__":
    output_path = "openapi.json"

    schema = app.openapi()

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
        print("OpenAPI JSON schema saved to openapi.json")
