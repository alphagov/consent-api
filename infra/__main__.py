"""A Google Cloud Python Pulumi program."""

import pulumi
import pulumi_gcp as gcp
from pulumi import Config
from pulumi import Output

config = Config()

network = gcp.compute.Network(
    "default",
    description="Default network for the project",
    name="default",
    routing_mode="REGIONAL",
)

private_ip = gcp.compute.GlobalAddress(
    "private_ip",
    address="10.125.80.0",
    address_type="INTERNAL",
    name="default-ip-range",
    network=network.id,
    prefix_length=20,
    purpose="VPC_PEERING",
)

peering_connection = gcp.servicenetworking.Connection(
    "peering_connection",
    network=network.name,
    reserved_peering_ranges=[private_ip.name],
    service="servicenetworking.googleapis.com",
)

db_instance = gcp.sql.DatabaseInstance(
    "main",
    database_version="POSTGRES_14",
    name="sde-consent-api-db",
    settings=gcp.sql.DatabaseInstanceSettingsArgs(
        deletion_protection_enabled=True,
        maintenance_window=gcp.sql.DatabaseInstanceSettingsMaintenanceWindowArgs(
            update_track="stable",
        ),
        ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
            ipv4_enabled=False,
            private_network=network.id,
        ),
        tier="db-f1-micro",
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[peering_connection],
    ),
)

database = gcp.sql.Database(
    "consent_api",
    charset="UTF8",
    collation="en_US.UTF8",
    instance=db_instance.name,
    name="consent_api",
)

users = gcp.sql.User(
    "users",
    instance=db_instance.name,
    name="postgres",
    # password=config.require_secret("db-password"),
)

database_url: Output = Output.secret(
    Output.format(
        "postgresql://postgres@/{host}?host=/cloudsql/{connection}",
        host=db_instance.private_ip_address,
        connection=db_instance.connection_name,
    )
)

github_service_account = gcp.serviceaccount.Account(
    "github_actions",
    account_id="github-actions",
    description="For pushing and deploying Docker images to Google Cloud",
    display_name="Github Actions",
)

wi_pool = gcp.iam.WorkloadIdentityPool(
    "default",
    description="Enable Github Actions to push to GCR",
    display_name="SDE Consent API Github Actions",
    workload_identity_pool_id="consent-api-github-actions",
)

wif_provider = gcp.iam.WorkloadIdentityPoolProvider(
    "default",
    attribute_mapping={
        "attribute.actor": "assertion.actor",
        "attribute.repository": "assertion.repository",
        "attribute.repository_owner": "assertion.repository_owner",
        "google.subject": "assertion.sub",
    },
    display_name="Github",
    oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
        issuer_uri="https://token.actions.githubusercontent.com",
    ),
    workload_identity_pool_id=wi_pool.workload_identity_pool_id,
    workload_identity_pool_provider_id="github",
)

github_iam = gcp.serviceaccount.IAMBinding(
    "github-iam",
    members=[
        Output.concat(
            "principalSet://iam.googleapis.com/",
            wi_pool.id,
            "/attribute.repository/alphagov/consent-api",
        ),
    ],
    role="roles/iam.workloadIdentityUser",
    service_account_id=github_service_account.name,
)

connector = gcp.vpcaccess.Connector(
    "default",
    ip_cidr_range="10.8.0.0/28",
    name="consent-api-serverless",
    network=network.id,
    max_throughput=1000,
)

vpc_connector_to_serverless = gcp.compute.Firewall(
    "vpc-connector-to-serverless",
    allows=[
        gcp.compute.FirewallAllowArgs(protocol="icmp"),
        gcp.compute.FirewallAllowArgs(ports=["665-666"], protocol="udp"),
        gcp.compute.FirewallAllowArgs(ports=["667"], protocol="tcp"),
    ],
    destination_ranges=["0.0.0.0/0"],
    direction="EGRESS",
    name="vpc-connector-to-serverless",
    network=network.id,
    source_ranges=[
        "107.178.230.64/26",
        "35.199.224.0/19",
    ],
    target_tags=["vpc-connector"],
)

serverless_to_vpc_connector = gcp.compute.Firewall(
    "serverless-to-vpc-connector",
    allows=[
        gcp.compute.FirewallAllowArgs(protocol="icmp"),
        gcp.compute.FirewallAllowArgs(ports=["665-666"], protocol="udp"),
        gcp.compute.FirewallAllowArgs(ports=["667"], protocol="tcp"),
    ],
    direction="INGRESS",
    name="serverless-to-vpc-connector",
    network=network.id,
    source_ranges=[
        "107.178.230.64/26",
        "35.199.224.0/19",
    ],
    target_tags=["vpc-connector"],
)

vpc_connector_requests = gcp.compute.Firewall(
    "vpc-connector-requests",
    allows=[
        gcp.compute.FirewallAllowArgs(protocol="icmp"),
        gcp.compute.FirewallAllowArgs(protocol="udp"),
        gcp.compute.FirewallAllowArgs(protocol="tcp"),
    ],
    direction="INGRESS",
    name="vpc-connector-requests",
    network=network.id,
    project="sde-consent-api",
    source_tags=["vpc-connector"],
)

vpc_connector_health_checks = gcp.compute.Firewall(
    "vpc-connector-health-checks",
    allows=[
        gcp.compute.FirewallAllowArgs(ports=["667"], protocol="tcp"),
    ],
    direction="INGRESS",
    name="vpc-connector-health-checks",
    network=network.id,
    project="sde-consent-api",
    source_ranges=[
        "130.211.0.0/22",
        "35.191.0.0/16",
        "108.170.220.0/23",
    ],
    target_tags=["vpc-connector"],
)

docker_image = "gcr.io/sde-consent-api/consent-api:v1.7.2"

consent_api = gcp.cloudrun.Service(
    "consent-api",
    location=Config("gcp").require("region"),
    name="consent-api",
    template=gcp.cloudrun.ServiceTemplateArgs(
        metadata=gcp.cloudrun.ServiceTemplateMetadataArgs(
            annotations={
                "autoscaling.knative.dev/maxScale": "5",
                "client.knative.dev/user-image": docker_image,
                "run.googleapis.com/cloudsql-instances": db_instance.connection_name,
                "run.googleapis.com/vpc-access-connector": connector.id,
                "run.googleapis.com/vpc-access-egress": "private-ranges-only",
            },
        ),
        spec=gcp.cloudrun.ServiceTemplateSpecArgs(
            containers=[
                gcp.cloudrun.ServiceTemplateSpecContainerArgs(
                    envs=[
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="DATABASE_URL",
                            value=database_url,
                        ),
                    ],
                    image=docker_image,
                )
            ],
            service_account_name="832060047369-compute@developer.gserviceaccount.com",
            timeout_seconds=300,
        ),
    ),
    traffics=[
        gcp.cloudrun.ServiceTrafficArgs(
            latest_revision=True,
            percent=100,
        )
    ],
)

pulumi.export("consent_api_url", consent_api.statuses[0].url)
pulumi.export("workload_identity_provider", wif_provider.name)
pulumi.export("service_account", github_service_account.email)
