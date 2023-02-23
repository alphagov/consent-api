"""A Google Cloud Python Pulumi program."""

import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()

stack = pulumi.get_stack()

project = gcp.projects.get_project(
    filter=f"id:{pulumi.Config('gcp').require('project')}",
).projects[0]

db_instance = gcp.sql.DatabaseInstance(
    "db-instance",
    database_version=config.require("db-version"),
    deletion_protection=False,
    settings=gcp.sql.DatabaseInstanceSettingsArgs(tier=config.require("db-tier")),
)

db = gcp.sql.Database(
    "db",
    instance=db_instance.name,
    name=config.require("db-name"),
)

db_user = gcp.sql.User(
    "db-user",
    instance=db_instance.name,
    name=config.require("db-name"),
    password=config.require_secret("db-password"),
)

db_url: pulumi.Output = pulumi.Output.secret(
    pulumi.Output.format(
        "postgresql://{user}:{password}@/{db}?host=/cloudsql/{connection}",
        user=db_user.name,
        password=db_user.password,
        db=db.name,
        connection=db_instance.connection_name,
    )
)

cloudrun_service = gcp.cloudrun.Service(
    "service",
    name=f"{stack}-consent-api",
    location=pulumi.Config("gcp").require("region"),
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
                    image="gcr.io/{project}/{image}".format(
                        project=project.project_id,
                        image=config.require("docker-image"),
                    ),
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

cloudrun_allow_public_access = gcp.cloudrun.IamBinding(
    "public-access-binding",
    location=cloudrun_service.location,
    service=cloudrun_service.name,
    role="roles/run.invoker",
    members=["allUsers"],
)

github_service_account = gcp.serviceaccount.Account(
    "service-account",
    account_id=f"{stack}",
    display_name=f"{stack.title()} Service Account",
)

github_wi_pool = gcp.iam.WorkloadIdentityPool(
    "workload-identity-pool",
    display_name="Github",
    workload_identity_pool_id="github",
)

github_wi_provider = gcp.iam.WorkloadIdentityPoolProvider(
    "workload-identity-pool-provider",
    workload_identity_pool_provider_id="github",
    display_name="Github",
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

github_service_account_binding = gcp.serviceaccount.IAMBinding(
    "github-oidc-service-account-binding",
    members=[github_oidc_member],
    role="roles/iam.workloadIdentityUser",
    service_account_id=github_service_account.name,
)

# TODO don't use the default service account
github_cloudrun_binding = gcp.serviceaccount.IAMBinding(
    "cloudrun-binding",
    members=[github_oidc_member],
    role="roles/iam.serviceAccountUser",
    service_account_id=gcp.compute.get_default_service_account().name,
)

github_access_to_storage_role = gcp.projects.IAMCustomRole(
    "access-to-storage-role",
    permissions=[
        "storage.buckets.get",
        "storage.objects.create",
        "storage.objects.delete",
        "storage.objects.list",
    ],
    role_id="pushToGCR",
    title="Push to GCR",
)

github_gcr_iam_binding = gcp.storage.BucketIAMBinding(
    "gcr-binding",
    bucket=gcp.storage.get_bucket(f"artifacts.{project.project_id}.appspot.com").name,
    members=[github_service_account.member],
    role=github_access_to_storage_role.name,
)

github_cloudrun_deploy_role = gcp.projects.IAMCustomRole(
    "cloudrun-deploy-role",
    permissions=[
        "run.services.get",
        "run.services.create",
        "run.services.update",
        "run.services.delete",
    ],
    role_id="cloudrunDeploy",
    title="Deploy Cloud Run Services",
)

github_allow_deploy = gcp.cloudrun.IamBinding(
    "cloudrun-binding",
    location=cloudrun_service.location,
    project=cloudrun_service.project,
    service=cloudrun_service.name,
    role=github_cloudrun_deploy_role.name,
    members=[github_service_account.member],
)

pulumi.export("consent_api_url", cloudrun_service.statuses[0].url)
pulumi.export("workload_identity_provider", github_wi_provider.name)
pulumi.export("service_account", github_service_account.email)
