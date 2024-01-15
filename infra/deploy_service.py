"""Pulumi inline program to deploy a stack."""

import argparse
from collections.abc import Callable
from pathlib import Path

import pulumi
from resources.abstract_resource import ResourceConfig
from resources.alerting_monitoring import AlertingMonitoring
from resources.cloudrun import CloudRun
from resources.database import Database
from resources.load_balancers import LoadBalancers
from ruamel.yaml import YAML


def deploy_service(env: str, branch: str | None, tag: str) -> Callable:
    """Wrapper around Pulumi inline program to pass in variables."""

    def _deploy() -> None:
        """Execute the inline Pulumi program."""
        config = ResourceConfig(
            env=env,
            tag=tag,
            branch=branch,
            stack=pulumi.get_stack(),
            region=pulumi.Config("gcp").require("region"),
            project_id=pulumi.Config("gcp").require("project"),
        )

        db = Database(config=config)
        cloud_run = CloudRun(config=config, db=db)
        AlertingMonitoring(config=config, cloud_run=cloud_run)
        LoadBalancers(config=config, cloud_run=cloud_run)

        if cloud_run.service is not None:
            pulumi.export("service_url", cloud_run.service.statuses[0].url)

    return _deploy


def main():
    """Deploy (or destroy) the service."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--destroy", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("-e", "--env", default="development")
    parser.add_argument("-b", "--branch", default="main")
    parser.add_argument("-t", "--tag")

    args = parser.parse_args()

    if args.env == "production":
        # Production doesn't support branch environments
        args.branch = None

    stack_name = args.env

    sanitised_branch = None
    if args.branch:
        sanitised_branch = args.branch.replace("/", "-")
        stack_name = f"{stack_name}-{sanitised_branch}"

    stack = pulumi.automation.create_or_select_stack(
        stack_name=stack_name,
        project_name="sde-consent-api",
        program=deploy_service(args.env, sanitised_branch, args.tag),
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
