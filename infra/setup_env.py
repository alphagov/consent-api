"""Pulumi inline program to deploy a stack."""

import argparse
from pathlib import Path

import pulumi
import pulumi_gcp as gcp
from ruamel.yaml import YAML


class EnvironmentStack:
    """Wrapper around Pulumi inline program to pass in variables."""

    def __init__(self, env: str) -> None:
        """Get the environment and optional tag."""
        self.env = env

    def __call__(self) -> None:
        """Execute the inline Pulumi program."""
        gcp.sql.DatabaseInstance(
            f"{self.env}-db-instance",
            database_version=pulumi.Config().require("db-version"),
            deletion_protection=False,
            settings=gcp.sql.DatabaseInstanceSettingsArgs(
                tier=pulumi.Config().require("db-tier")
            ),
        )

        github_service_account = gcp.serviceaccount.Account(
            "service-account",
            account_id=f"{self.env}",
            display_name=f"{self.env.title()} Service Account",
        )

        github_wi_pool = gcp.iam.WorkloadIdentityPool.get(
            "workload-identity-pool",
            id=f"{self.env}-github-wi-pool",
        )
        if not github_wi_pool:
            github_wi_pool = gcp.iam.WorkloadIdentityPool(
                "workload-identity-pool",
                display_name=f"{self.env.title()} Github WI pool",
                workload_identity_pool_id=f"{self.env}-github-wi-pool",
            )

        github_wi_provider = gcp.iam.WorkloadIdentityPoolProvider.get(
            "workload-identity-pool-provider",
            id=pulumi.Output.concat(
                github_wi_pool.name,
                f"/providers/{self.env}-github-wi-provider",
            ),
        )
        if not github_wi_provider:
            github_wi_provider = gcp.iam.WorkloadIdentityPoolProvider(
                "workload-identity-pool-provider",
                workload_identity_pool_provider_id=f"{self.env}-github-wi-provider",
                display_name=f"{self.env.title()} Github",
                workload_identity_pool_id=github_wi_pool.workload_identity_pool_id,
                oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
                    issuer_uri="https://token.actions.githubusercontent.com",
                ),
                attribute_mapping={
                    "attribute.actor": "assertion.actor",
                    "attribute.repository": "assertion.repository",
                    "attribute.repository_owner": "assertion.repository_owner",
                    "google.subject": "assertion.sub",
                },
            )

        github_oidc_member = pulumi.Output.format(
            "principalSet://iam.googleapis.com/{wi_pool}/attribute.repository/{repo}",
            wi_pool=github_wi_pool.name,
            repo="alphagov/consent-api",
        )

        gcp.serviceaccount.IAMBinding(
            "github-oidc-service-account-binding",
            members=[github_oidc_member],
            role="roles/iam.workloadIdentityUser",
            service_account_id=github_service_account.name,
        )

        gcp.serviceaccount.IAMBinding(
            "cloudrun-binding",
            members=[github_service_account.member],
            role="roles/iam.serviceAccountUser",
            service_account_id=gcp.compute.get_default_service_account().name,
        )

        gcp.projects.IAMMember(
            "project",
            member=github_service_account.member,
            project="sde-consent-api",
            role="roles/cloudsql.viewer",
        )

        github_access_to_storage_role = gcp.projects.IAMCustomRole(
            "access-to-storage-role",
            permissions=[
                "storage.buckets.get",
                "storage.objects.create",
                "storage.objects.delete",
                "storage.objects.get",
                "storage.objects.list",
            ],
            role_id=f"{self.env}_pushToGCR",
            title=f"{self.env.title()} push to GCR",
        )

        gcp.storage.BucketIAMBinding(
            "gcr-binding",
            bucket=gcp.storage.get_bucket("artifacts.sde-consent-api.appspot.com").name,
            members=[github_service_account.member],
            role=github_access_to_storage_role.name,
        )

        pulumi.export("workload_identity_provider", github_wi_provider.name)
        pulumi.export("service_account", github_service_account.email)


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
        program=EnvironmentStack(args.env),
        work_dir=Path(__file__).parent.parent,
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
