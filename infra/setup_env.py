"""Pulumi inline program to deploy a stack."""
# comment
import argparse
from collections.abc import Callable
from pathlib import Path

import pulumi
from pulumi_gcp import compute
from pulumi_gcp import iam
from pulumi_gcp import projects
from pulumi_gcp import serviceaccount
from pulumi_gcp import sql
from pulumi_gcp import storage
from ruamel.yaml import YAML

# Setup the project before deployments
# DB instance
# Github deploy service account with Workload Identity Pools
# IAM permissions


def setup_env(env: str) -> Callable:
    """Wrapper around Pulumi inline program to pass in variables."""

    def _setup() -> None:
        """Execute the inline Pulumi program."""
        sql.DatabaseInstance(
            f"{env}-db-instance",
            database_version=pulumi.Config().require("db-version"),
            deletion_protection=False,
            settings={"tier": pulumi.Config().require("db-tier")},
        )

        sa = serviceaccount.Account(
            "service-account",
            account_id=f"{env}",
            display_name=f"{env.title()} Service Account",
        )

        wi_pool = iam.WorkloadIdentityPool.get(
            "workload-identity-pool",
            id=f"{env}-github-wi-pool",
        )
        if not wi_pool:
            wi_pool = iam.WorkloadIdentityPool(
                "workload-identity-pool",
                display_name=f"{env.title()} Github WI pool",
                workload_identity_pool_id=f"{env}-github-wi-pool",
            )

        wi_provider = iam.WorkloadIdentityPoolProvider.get(
            "workload-identity-pool-provider",
            id=pulumi.Output.concat(
                wi_pool.name,
                f"/providers/{env}-github-wi-provider",
            ),
        )
        if not wi_provider:
            wi_provider = iam.WorkloadIdentityPoolProvider(
                "workload-identity-pool-provider",
                workload_identity_pool_provider_id=f"{env}-github-wi-provider",
                display_name=f"{env.title()} Github",
                workload_identity_pool_id=wi_pool.workload_identity_pool_id,
                oidc={
                    "issuer_uri": "https://token.actions.githubusercontent.com",
                },
                attribute_mapping={
                    "attribute.actor": "assertion.actor",
                    "attribute.repository": "assertion.repository",
                    "attribute.repository_owner": "assertion.repository_owner",
                    "google.subject": "assertion.sub",
                },
            )

        github_oidc_member = pulumi.Output.format(
            "principalSet://iam.googleapis.com/{wi_pool}/attribute.repository/{repo}",
            wi_pool=wi_pool.name,
            repo="alphagov/consent-api",
        )

        serviceaccount.IAMBinding(
            "github-oidc-service-account-binding",
            members=[github_oidc_member],
            role="roles/iam.workloadIdentityUser",
            service_account_id=sa.name,
        )

        serviceaccount.IAMBinding(
            "cloudrun-binding",
            members=[sa.member],
            role="roles/iam.serviceAccountUser",
            service_account_id=compute.get_default_service_account().name,
        )

        deployment_role = projects.IAMCustomRole(
            "deployment-role",
            permissions=[
                "cloudsql.databases.create",
                "cloudsql.databases.delete",
                "cloudsql.databases.get",
                "cloudsql.databases.update",
                "cloudsql.instances.get",
                "cloudsql.instances.list",
                "cloudsql.users.create",
                "cloudsql.users.delete",
                "cloudsql.users.get",
                "cloudsql.users.list",
                "cloudsql.users.update",
                "resourcemanager.projects.get",
                "run.services.create",
                "run.services.delete",
                "run.services.get",
                "run.services.getIamPolicy",
                "run.services.setIamPolicy",
                "run.services.update",
                # Load Balancer permissions below
                "compute.backendServices.create",
                "compute.backendServices.delete",
                "compute.backendServices.get",
                "compute.backendServices.use",
                "compute.forwardingRules.create",
                "compute.forwardingRules.delete",
                "compute.forwardingRules.get",
                "compute.forwardingRules.use",
                "compute.globalAddresses.create",
                "compute.globalAddresses.delete",
                "compute.globalAddresses.get",
                "compute.globalAddresses.use",
                "compute.networkEndpointGroups.create",
                "compute.networkEndpointGroups.delete",
                "compute.networkEndpointGroups.get",
                "compute.networkEndpointGroups.use",
                "compute.regionNetworkEndpointGroups.create",
                "compute.regionNetworkEndpointGroups.get",
                "compute.regionNetworkEndpointGroups.use",
                "compute.regionNetworkEndpointGroups.delete",
                "compute.regionOperations.get",
                "compute.sslCertificates.create",
                "compute.sslCertificates.delete",
                "compute.sslCertificates.get",
                "compute.targetHttpProxies.create",
                "compute.targetHttpProxies.get",
                "compute.targetHttpProxies.delete",
                "compute.targetHttpProxies.use",
                "compute.targetHttpsProxies.create",
                "compute.targetHttpsProxies.get",
                "compute.targetHttpsProxies.delete",
                "compute.targetHttpsProxies.use",
                "compute.urlMaps.create",
                "compute.urlMaps.get",
                "compute.urlMaps.delete",
                "compute.urlMaps.use",
                "compute.globalForwardingRules.create",
                "compute.globalForwardingRules.get",
                "compute.globalForwardingRules.delete",
            ],
            role_id=f"{env}_deploy",
            title=f"{env.title()} deployment",
        )

        projects.IAMMember(
            "project-deployer",
            member=sa.member,
            project="sde-consent-api",
            role=deployment_role.name,
        )

        projects.IAMMember(
            "project-cloudsql",
            member=sa.member,
            project="sde-consent-api",
            role="roles/cloudsql.admin",
        )

        access_to_storage_role = projects.IAMCustomRole(
            "access-to-storage-role",
            permissions=[
                "storage.buckets.get",
                "storage.objects.create",
                "storage.objects.delete",
                "storage.objects.get",
                "storage.objects.list",
            ],
            role_id=f"{env}_pushToGCR",
            title=f"{env.title()} push to GCR",
        )

        storage.BucketIAMBinding(
            "gcr-binding",
            bucket=storage.get_bucket("artifacts.sde-consent-api.appspot.com").name,
            members=[sa.member],
            role=access_to_storage_role.name,
        )

        pulumi.export("workload_identity_provider", wi_provider.name)
        pulumi.export("service_account", sa.email)

    return _setup


def main():
    """Spin up (or down) the environment."""
    parser = argparse.ArgumentParser(description="Spin up an environment")
    parser.add_argument(
        "--destroy", action="store_true", help="Destroy the environment"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help=(
            "Do not actually create or update the environment, but preview what "
            "would be done"
        ),
    )
    parser.add_argument(
        "-e", "--env", default="development", help="Name of the environment"
    )

    args = parser.parse_args()

    stack_name = args.env

    stack = pulumi.automation.create_or_select_stack(
        stack_name=stack_name,
        project_name="sde-consent-api",
        program=setup_env(args.env),
        work_dir=Path(__file__).parent.parent,
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
