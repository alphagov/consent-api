"""Pulumi inline program to deploy a stack."""

import argparse
import secrets
import string
import subprocess
from collections.abc import Callable
from pathlib import Path

import pulumi
from pulumi_gcp import cloudrun
from pulumi_gcp import sql
from ruamel.yaml import YAML


def generate_password(length: int = 20) -> pulumi.Output[str]:
    """Generate a random password."""
    alphabet = string.ascii_letters + string.digits
    return pulumi.Output.secret(
        "".join(secrets.choice(alphabet) for i in range(length)),
    )


def get_db_instance_id(env: str) -> str:
    """Get an existing database instance in the given environment (if one exists)."""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "sql",
                "instances",
                "list",
                "--project",
                "sde-consent-api",
                "--format",
                "value(name)",
                "--filter",
                f"name:{env}-*",
            ],
            check=True,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as err:
        print("Failed getting existing database instance")
        print(f"{err.returncode=}")
        print(err.output)
        raise
    return result.stdout.strip()


def deploy_service(env: str, branch: str, tag: str) -> Callable:
    """Wrapper around Pulumi inline program to pass in variables."""

    def _deploy() -> None:
        """Execute the inline Pulumi program."""
        name = "consent-api"
        if branch:
            name = f"{name}--{branch}"

        google_project = "sde-consent-api"

        stack = pulumi.get_stack()

        db_instance = sql.DatabaseInstance.get(
            f"{env}-db-instance",
            get_db_instance_id(env),
        )
        db_connection = db_instance.connection_name

        db = sql.Database(
            f"{name}--db",
            name=name,
            instance=db_instance.name,
        )

        db_user = sql.User(
            f"{name}--db-user",
            name=name,
            instance=db_instance.name,
            password=generate_password(),
        )

        db_url: pulumi.Output = pulumi.Output.secret(
            pulumi.Output.format(
                "{dialect}://{user}:{password}@/{db}?host=/cloudsql/{connection}",
                dialect="postgresql+asyncpg",
                user=db_user.name,
                password=db_user.password,
                db=db.name,
                connection=db_connection,
            )
        )

        service = cloudrun.Service(
            name,
            name=f"{stack}-consent-api",
            location=pulumi.Config("gcp").require("region"),
            template={
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/maxScale": "5",
                        "run.googleapis.com/cloudsql-instances": db_connection,
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "image": f"gcr.io/{google_project}/consent-api:{tag}",
                            "envs": [
                                {"name": "DATABASE_URL", "value": db_url},
                                {"name": "ENV", "value": stack},
                            ],
                        },
                    ],
                },
            },
            traffics=[
                {
                    "latest_revision": True,
                    "percent": 100,
                },
            ],
        )

        # TODO only allow public access to production - other envs should be behind some
        # kind of auth
        cloudrun.IamBinding(
            f"{name}--public-access-binding",
            location=service.location,
            service=service.name,
            role="roles/run.invoker",
            members=["allUsers"],
        )

        pulumi.export("service_url", service.statuses[0].url)

    return _deploy


def main():
    """Deploy (or destroy) the service."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--destroy", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("-e", "--env", default="development")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-b", "--branch", default="main")
    group.add_argument("-t", "--tag")

    args = parser.parse_args()

    stack_name = args.env
    if args.branch:
        stack_name = f"{stack_name}-{args.branch}"

    stack = pulumi.automation.create_or_select_stack(
        stack_name=stack_name,
        project_name="sde-consent-api",
        program=deploy_service(args.env, args.branch, args.tag),
    )
    print(f"Initialised stack {stack_name}")

    print("Installing plugins...")
    stack.workspace.install_plugin("gcp", "v6.67.0")

    config_file = Path(__file__).parent / "config" / f"Pulumi.{args.env}.yaml"
    config = YAML(typ="safe").load(config_file)
    for name, value in config["config"].items():
        stack.set_config(name, pulumi.automation.ConfigValue(value=value))

    stack.refresh(on_output=print)

    result = None
    if args.destroy:
        print("Destroying stack...")
        stack.destroy(on_output=print)

    elif args.preview:
        stack.preview(on_output=print)

    else:
        print("Updating stack...")
        result = stack.up(on_output=print)
        for name, output in result.outputs.items():
            print(f"{name}: {output.value}")


if __name__ == "__main__":
    main()
