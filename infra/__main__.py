"""A Google Cloud Python Pulumi program."""

import pulumi
import pulumi_gcp as gcp
from pulumi import Config
from pulumi import Output

config = Config()
project = gcp.projects.get_project(filter="id:sde-consent-api")

db_instance = gcp.sql.DatabaseInstance(
    "consent-postgres-db-instance",
    database_version="POSTGRES_14",
    deletion_protection=False,
    settings=gcp.sql.DatabaseInstanceSettingsArgs(tier="db-f1-micro"),
)

database = gcp.sql.Database(
    "consent-db",
    instance=db_instance.name,
    name=config.require("db-name"),
)

users = gcp.sql.User(
    "consent-db-user",
    instance=db_instance.name,
    name=config.require("db-name"),
    password=config.require_secret("db-password"),
)

github_service_account = gcp.serviceaccount.Account(
    "github-service-account",
    account_id="github",
    display_name="Github",
)

wi_pool = gcp.iam.WorkloadIdentityPool(
    "default",
    display_name="Github",
    workload_identity_pool_id="github-actions",
)

wif_provider = gcp.iam.WorkloadIdentityPoolProvider(
    "github-wi-provider",
    attribute_mapping={
        "attribute.actor": "assertion.actor",
        "attribute.repository": "assertion.repository",
        "attribute.repository_owner": "assertion.repository_owner",
        "google.subject": "assertion.sub",
    },
    display_name="Github",
    description="Github OIDC identity pool provider for Github Actions",
    oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
        issuer_uri="https://token.actions.githubusercontent.com",
    ),
    workload_identity_pool_id=wi_pool.workload_identity_pool_id,
    workload_identity_pool_provider_id="github",
)

github_member = Output.format(
    "principalSet://iam.googleapis.com/{wi_pool}/attribute.repository/{repo}",
    wi_pool=wi_pool.name,
    repo="alphagov/consent-api",
)

github_iam = gcp.serviceaccount.IAMBinding(
    "github-iam-binding",
    members=[github_member],
    role="roles/iam.workloadIdentityUser",
    service_account_id=github_service_account.name,
)

github_assume_cloudrun_role = gcp.serviceaccount.IAMBinding(
    "github-cloudrun-binding",
    members=[github_service_account.member],
    role="roles/iam.serviceAccountUser",
    service_account_id=Output.format(
        "projects/{project_id}/serviceAccounts/{sa_email}",
        project_id="sde-consent-api",
        sa_email=Output.concat(
            project.projects[0].number,
            "-compute@developer.gserviceaccount.com",
        ),
    ),
)

github_storage_role = gcp.projects.IAMCustomRole(
    "github-access-to-storage",
    description="Role for Github Actions user to read and write GCR images",
    permissions=[
        "storage.buckets.get",
        "storage.objects.create",
        "storage.objects.delete",
        "storage.objects.list",
    ],
    role_id="githubStorageRole",
    title="Github Storage Role",
)

github_gcr_role = gcp.storage.BucketIAMBinding(
    "github-gcr-binding",
    bucket=gcp.storage.get_bucket(name="artifacts.sde-consent-api.appspot.com").name,
    members=[github_service_account.member],
    role=github_storage_role.name,
)

github_deploy_role = gcp.projects.IAMCustomRole(
    "github-cloudrun-deploy",
    description="Role for Github Actions user to deploy to Cloud Run",
    permissions=[
        "run.services.get",
        "run.services.create",
        "run.services.update",
        "run.services.delete",
    ],
    role_id="githubDeployRole",
    title="Github Deploy Role",
)

db_password: Output = Output.secret(
    Output.format(
        "postgresql://{user}:{password}@/{host}?host=/cloudsql/{connection}",
        user=config.require("db-name"),
        password=config.require_secret("db-password"),
        host=config.require("db-name"),
        connection=db_instance.connection_name,
    )
)

consent_api = gcp.cloudrun.Service(
    "consent-api-service",
    name="consent-api",
    location=Config("gcp").require("region"),
    template=gcp.cloudrun.ServiceTemplateArgs(
        metadata=gcp.cloudrun.ServiceTemplateMetadataArgs(
            annotations={
                "autoscaling.knative.dev/maxScale": "5",
                "run.googleapis.com/cloudsql-instances": db_instance.connection_name,
            },
        ),
        spec=gcp.cloudrun.ServiceTemplateSpecArgs(
            containers=[
                gcp.cloudrun.ServiceTemplateSpecContainerArgs(
                    image="gcr.io/sde-consent-api/consent-api:v1.7.2",
                    envs=[
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="DATABASE_URL",
                            value=db_password,
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

github_deploy_binding = gcp.cloudrun.IamBinding(
    "github-deploy-binding",
    location=consent_api.location,
    project=consent_api.project,
    service=consent_api.name,
    role=github_deploy_role.name,
    members=[github_service_account.member],
)

public_access = gcp.cloudrun.IamBinding(
    "public-access",
    location=consent_api.location,
    service=consent_api.name,
    role="roles/run.invoker",
    members=["allUsers"],
)


pulumi.export("consent_api_url", consent_api.statuses[0].url)
pulumi.export("workload_identity_provider", wif_provider.name)
pulumi.export("service_account", github_service_account.email)
