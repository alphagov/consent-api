"""Pulumi inline program to deploy a stack."""

import argparse
from collections.abc import Callable
from pathlib import Path

import pulumi
from resources.abstract_resource import ResourceConfig
from resources.alerting_monitoring import AlertingMonitoring
from resources.cloudrun import CloudRun
from resources.database import Database
from resources.iam import Iam
from resources.load_balancers import LoadBalancers
from ruamel.yaml import YAML
from types_ import EnvType


def deploy_service(tag: str, env: EnvType) -> Callable:
    """Wrapper around Pulumi inline program to pass in variables."""

    def _deploy() -> None:
        """Execute the inline Pulumi program."""
        config = ResourceConfig(
            tag=tag,
            env=env,
            stack=pulumi.get_stack(),
            region=pulumi.Config("gcp").require("region"),
            project_id=pulumi.Config("gcp").require("project"),
        )

        Iam(config=config)
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
    parser.add_argument("-s", "--stack", default="development")
    parser.add_argument("-t", "--tag", default="latest")

    args = parser.parse_args()

    stack_name = args.stack

    if stack_name.startswith("dev"):
        config_env: EnvType = "development"
    elif stack_name.startswith("staging"):
        config_env: EnvType = "staging"
    elif stack_name.startswith("prod"):
        config_env: EnvType = "production"
    else:
        raise ValueError(f"Unknown stack name: {stack_name}")

    stack = pulumi.automation.create_or_select_stack(
        stack_name=stack_name,
        project_name="sde-consent-api",
        program=deploy_service(args.tag, config_env),
    )
    print(f"Initialised stack {stack_name}")

    print("Installing plugins...")
    stack.workspace.install_plugin("gcp", "v6.67.0")

    config_file = Path(__file__).parent / "config" / f"Pulumi.{config_env}.yaml"
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
