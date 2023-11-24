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
from utils import ProductionColor
from utils import configure_cloud_run_traffics
from utils import get_latest_production_revision
from utils import get_opposite_production_color


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


def resource_name(template: str, trimmable: str | None) -> str:
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
    trimmed = trimmable[:max_length] if trimmable else ""

    return template.replace("$", trimmed).replace("/", "-")


def deploy_service(env: str, branch: str | None, tag: str) -> Callable:
    """Wrapper around Pulumi inline program to pass in variables."""

    def _deploy() -> None:
        """Execute the inline Pulumi program."""

        region = pulumi.Config("gcp").require("region")
        project_id = pulumi.Config("gcp").require("project")
        name = "consent-api"
        if branch:
            name = f"{name}--{branch}"

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

        cloudrun_service_name = resource_name("$-consent-api", stack)
        if env == "production":
            print("🚀 Deploying new Cloud Run revision to production")
            dot = {
                ProductionColor.GREEN: "🟢",
                ProductionColor.BLUE: "🔵",
            }
            latest_color, latest_rev_name = get_latest_production_revision(
                project_id=project_id, region=region, service_name=cloudrun_service_name
            )
            next_color = get_opposite_production_color(latest_color)
            print(f"{dot[latest_color]} Latest color was {latest_color.value}")
            print(f"{dot[next_color]} Deploying to {next_color.value}")

        cloud_run_traffics = configure_cloud_run_traffics(
            env, next_color, latest_color, latest_rev_name
        )

        service = cloudrun.Service(
            name,
            name=cloudrun_service_name,
            location=region,
            template={
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/maxScale": "5",
                        "run.googleapis.com/cloudsql-instances": db_connection,
                        "production-color": next_color.value,
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "image": f"gcr.io/{project_id}/consent-api:{tag}",
                            "envs": [
                                {"name": "DATABASE_URL", "value": db_url},
                                {"name": "ENV", "value": env},
                            ],
                        },
                    ],
                },
            },
            traffics=cloud_run_traffics,
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
            project=project_id,
        )

        endpoint_group = compute.RegionNetworkEndpointGroup(
            resource_name(f"{env}--$--endpoint-group", name),
            network_endpoint_type="SERVERLESS",
            region=region,
            cloud_run=compute.RegionNetworkEndpointGroupCloudRunArgs(
                service=service.name
            ),
        )

        rate_limiting_rule = compute.SecurityPolicyRuleArgs(
            priority=1000,
            action="rate_based_ban",
            match=compute.SecurityPolicyRuleMatchArgs(
                versioned_expr="SRC_IPS_V1",
                config=compute.SecurityPolicyRuleMatchConfigArgs(src_ip_ranges=["*"]),
            ),
            rate_limit_options=compute.SecurityPolicyRuleRateLimitOptionsArgs(
                conform_action="allow",
                exceed_action="deny(403)",
                rate_limit_threshold=compute.SecurityPolicyRuleRateLimitOptionsRateLimitThresholdArgs(
                    count=500, interval_sec=10
                ),
                ban_duration_sec=60,
                enforce_on_key="IP",
            ),
        )

        security_policy = compute.SecurityPolicy(
            resource_name=resource_name(f"{env}--$--security-policy", branch),
            rules=[rate_limiting_rule],
        )

        backend_service = compute.BackendService(
            resource_name(f"{env}--$--backend-service", name),
            enable_cdn=False,
            connection_draining_timeout_sec=10,
            log_config=compute.BackendServiceLogConfigArgs(
                enable=True, sample_rate=0.5
            ),
            backends=[compute.BackendServiceBackendArgs(group=endpoint_group.id)],
            security_policy=security_policy.self_link,
        )

        # https_map sends all incoming https traffic to the designated backend service
        https_path_matcher_name = resource_name(f"{env}--$--https--path-matcher", name)
        https_paths = compute.URLMap(
            resource_name(f"{env}--$--https--load-balancer", name),
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
