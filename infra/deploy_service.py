"""Pulumi inline program to deploy a stack."""

import argparse
import secrets
import string
import subprocess
from pathlib import Path

import pulumi
import pulumi_gcp as gcp
from ruamel.yaml import YAML


def generate_password(length=20) -> pulumi.Output[str]:
    """Generate a random password."""
    alphabet = string.ascii_letters + string.digits
    return pulumi.Output.secret(
        "".join(secrets.choice(alphabet) for i in range(length)),
    )


def get_db_instance_id(env: str) -> str | None:
    """Get an existing database instance in the given environment (if one exists)."""
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
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    return None


class ConsentAPIStack:
    """Wrapper around Pulumi inline program to pass in variables."""

    def __init__(self, env: str, branch: str, tag: str) -> None:
        """Get the environment and optional tag."""
        self.env = env
        self.branch = branch
        self.tag = tag or branch

    def __call__(self) -> None:
        """Execute the inline Pulumi program."""
        name = "consent-api"
        if self.branch:
            name = f"{name}--{self.branch}"

        google_project = "sde-consent-api"

        stack = pulumi.get_stack()

        db_instance = gcp.sql.DatabaseInstance.get(
            f"{self.env}-db-instance",
            get_db_instance_id(self.env),
        )
        db_connection = db_instance.connection_name

        db = gcp.sql.Database(
            f"{name}--db",
            name=name,
            instance=db_instance.name,
        )

        db_user = gcp.sql.User(
            f"{name}--db-user",
            name=name,
            instance=db_instance.name,
            password=generate_password(length=20),
        )

        db_url: pulumi.Output = pulumi.Output.secret(
            pulumi.Output.format(
                "postgresql://{user}:{password}@/{db}?host=/cloudsql/{connection}",
                user=db_user.name,
                password=db_user.password,
                db=db.name,
                connection=db_connection,
            )
        )

        service = gcp.cloudrun.Service(
            name,
            name=f"{stack}-consent-api",
            location=pulumi.Config("gcp").require("region"),
            template=gcp.cloudrun.ServiceTemplateArgs(
                metadata=gcp.cloudrun.ServiceTemplateMetadataArgs(
                    annotations={
                        "autoscaling.knative.dev/maxScale": "5",
                        "run.googleapis.com/cloudsql-instances": db_connection,
                    },
                ),
                spec=gcp.cloudrun.ServiceTemplateSpecArgs(
                    containers=[
                        gcp.cloudrun.ServiceTemplateSpecContainerArgs(
                            image=f"gcr.io/{google_project}/consent-api:{self.tag}",
                            envs=[
                                gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                                    name="DATABASE_URL",
                                    value=db_url,
                                ),
                                gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                                    name="ENV",
                                    value=stack,
                                ),
                            ],
                        )
                    ],
                ),
            ),
            traffics=[
                gcp.cloudrun.ServiceTrafficArgs(
                    latest_revision=True,
                    percent=100,
                )
            ],
        )

        # TODO only allow public access to production - other envs should be behind some
        # kind of auth
        gcp.cloudrun.IamBinding(
            f"{name}--public-access-binding",
            location=service.location,
            service=service.name,
            role="roles/run.invoker",
            members=["allUsers"],
        )

        pulumi.export("service_url", service.statuses[0].url)


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
        program=ConsentAPIStack(args.env, args.branch, args.tag),
    )
    print(f"Initialised stack {stack_name}")

    print("Installing plugins...")
    stack.workspace.install_plugin("gcp", "v6.52.0")

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
