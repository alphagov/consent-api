"""Pulumi inline program to deploy a stack."""

import argparse
import secrets
import string
import subprocess
from collections.abc import Callable
from pathlib import Path

import pulumi
from pulumi_gcp import cloudrun
from pulumi_gcp import compute
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


def resource_name(template: str, trimmable: str) -> str:
    """
    Generate a name for a resource.

    Length is limited to 63
    @trimmable will be trimmed if necessary

    @template: the name template in format "prefix-$-suffix"
    Where $ will be replaced with @trimmable
    """

    commit_hash_length = 7
    max_length = 63 - len(template) - commit_hash_length
    max_length -= 2  # some contingency
    trimmed = trimmable[:max_length]

    return template.replace("$", trimmed).replace("/", "-")


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
            resource_name("$--db", name),
            name=name,
            instance=db_instance.name,
        )

        db_user = sql.User(
            resource_name("$--db-user", name),
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
            name=resource_name("$-consent-api", stack),
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
                                {"name": "ENV", "value": env},
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
            resource_name("$--public-access-binding", name),
            location=service.location,
            service=service.name,
            role="roles/run.invoker",
            members=["allUsers"],
        )

        # Now we set up the Load Balancer for the cloud run service
        # It will have a public facing IP as well as a DNS record with an SSL cert

        ip_address = compute.GlobalAddress(
            resource_name(f"{env}--$--ipaddress", name),
            address_type="EXTERNAL",
            project=google_project,
        )

        endpoint_group = compute.RegionNetworkEndpointGroup(
            resource_name(f"{env}--$--endpoint-group", name),
            network_endpoint_type="SERVERLESS",
            region=pulumi.Config("gcp").require("region"),
            cloud_run=compute.RegionNetworkEndpointGroupCloudRunArgs(
                service=service.name
            ),
        )

        backend_service = compute.BackendService(
            resource_name(f"{env}--$--backend-service", name),
            enable_cdn=False,
            connection_draining_timeout_sec=10,
            log_config=compute.BackendServiceLogConfigArgs(
                enable=True, sample_rate=0.5
            ),
            backends=[compute.BackendServiceBackendArgs(group=endpoint_group.id)],
        )

        # https_map sends all incoming https traffic to the designated backend service
        https_path_matcher_name = resource_name(f"{env}--$--https--path-matcher", name)
        https_paths = compute.URLMap(
            f"{env}--{branch}--https--load-balancer",
            default_service=backend_service.id,
            host_rules=[
                compute.URLMapHostRuleArgs(
                    hosts=[pulumi.Config("sde-consent-api").require("domain")],
                    path_matcher=https_path_matcher_name,
                )
            ],
            path_matchers=[
                compute.URLMapPathMatcherArgs(
                    name=https_path_matcher_name,
                    default_service=backend_service.id,
                    path_rules=[
                        compute.URLMapPathMatcherPathRuleArgs(
                            paths=["/*"],
                            service=backend_service.id,
                        )
                    ],
                )
            ],
        )

        certificate = compute.ManagedSslCertificate(
            resource_name(f"{env}--$--certificate", name),
            managed=compute.ManagedSslCertificateManagedArgs(
                domains=[pulumi.Config("sde-consent-api").require("domain")],
            ),
        )

        https_proxy = compute.TargetHttpsProxy(
            resource_name=resource_name(f"{env}--$--https-proxy", name),
            url_map=https_paths.id,
            ssl_certificates=[certificate.id],
        )

        compute.GlobalForwardingRule(
            resource_name=f"{env}--https--forwarding-rule",
            target=https_proxy.self_link,
            ip_address=ip_address.address,
            port_range="443",
            load_balancing_scheme="EXTERNAL",
        )

        # http_paths redirects any http incoming traffic to its https equivalent
        http_path_matcher_name = resource_name(f"{env}--$--http--path-matcher", name)
        http_paths = compute.URLMap(
            resource_name(f"{env}--$--http--load-balancer", branch),
            default_service=backend_service.id,
            host_rules=[
                compute.URLMapHostRuleArgs(
                    hosts=[pulumi.Config("sde-consent-api").require("domain")],
                    path_matcher=http_path_matcher_name,
                )
            ],
            path_matchers=[
                compute.URLMapPathMatcherArgs(
                    name=http_path_matcher_name,
                    default_service=backend_service.id,
                    path_rules=[
                        compute.URLMapPathMatcherPathRuleArgs(
                            paths=["/*"],
                            url_redirect=compute.URLMapPathMatcherPathRuleUrlRedirectArgs(
                                strip_query=False, https_redirect=True
                            ),
                        )
                    ],
                )
            ],
        )

        http_proxy = compute.TargetHttpProxy(
            resource_name=resource_name(f"{env}--$--http-proxy", name),
            url_map=http_paths.id,
        )

        compute.GlobalForwardingRule(
            resource_name=f"{env}--http-forwarding-rule",
            target=http_proxy.self_link,
            ip_address=ip_address.address,
            port_range="80",
            load_balancing_scheme="EXTERNAL",
        )

        pulumi.export("service_url", service.statuses[0].url)

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

    stack_name = args.env
    sanitised_branch = args.branch.replace("/", "-") if args.branch else ""
    if args.branch:
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
