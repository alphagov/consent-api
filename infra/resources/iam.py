from dataclasses import dataclass

import pulumi
from pulumi_gcp import compute
from pulumi_gcp import iam
from pulumi_gcp import projects
from pulumi_gcp import serviceaccount
from pulumi_gcp import storage

from resources import AbstractResource


@dataclass
class Iam(AbstractResource):
    def _create(self) -> None:
        self.sa = serviceaccount.Account(
            "service-account",
            account_id=f"{self.config.stack}",
            display_name=f"{self.config.stack} Service Account",
        )

        # WARNING: one wi_pool per environment, not stack
        # Shared across stacks of the same environment
        self.wi_pool = iam.WorkloadIdentityPool.get(
            "workload-identity-pool",
            id=f"{self.config.env}-github-wi-pool",
        )
        if not self.wi_pool:
            print("No pool found, creating one")
            self.wi_pool = iam.WorkloadIdentityPool(
                "workload-identity-pool",
                display_name=f"{self.config.env} Github WI pool",
                workload_identity_pool_id=f"{self.config.env}-github-wi-pool",
            )

        # WARNING: one wi_provider per environment, not stack
        # Shared across stacks of the same environment
        self.wi_provider = iam.WorkloadIdentityPoolProvider.get(
            "workload-identity-pool-provider",
            id=pulumi.Output.concat(
                self.wi_pool.name,
                f"/providers/{self.config.env}-github-wi-provider",
            ),
        )
        if not self.wi_provider:
            print("No pool provider, creating one")
            self.wi_provider = iam.WorkloadIdentityPoolProvider(
                "workload-identity-self.pool-provider",
                workload_identity_pool_provider_id=f"{self.config.env}-github-wi-provider",
                display_name=f"{self.config.stack} Github",
                workload_identity_pool_id=self.wi_pool.id,
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
            wi_pool=self.wi_pool.name,
            repo="alphagov/consent-api",
        )

        serviceaccount.IAMBinding(
            "github-oidc-service-account-binding",
            members=[github_oidc_member],
            role="roles/iam.workloadIdentityUser",
            service_account_id=self.sa.name,
        )

        serviceaccount.IAMBinding(
            "cloudrun-binding",
            members=[self.sa.member],
            role="roles/iam.serviceAccountUser",
            service_account_id=compute.get_default_service_account().name,
        )

        self.deployment_role = projects.IAMCustomRole(
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
                "compute.targetHttpProxies.setUrlMap",
                "compute.targetHttpsProxies.create",
                "compute.targetHttpsProxies.get",
                "compute.targetHttpsProxies.delete",
                "compute.targetHttpsProxies.use",
                "compute.targetHttpsProxies.setUrlMap",
                "compute.urlMaps.create",
                "compute.urlMaps.get",
                "compute.urlMaps.delete",
                "compute.urlMaps.use",
                "compute.globalForwardingRules.create",
                "compute.globalForwardingRules.get",
                "compute.globalForwardingRules.delete",
            ],
            role_id=f"{self._format_role(self.config.stack)}_deploy",
            title=f"{self.config.stack} deployment",
        )

        projects.IAMMember(
            "project-deployer",
            member=self.sa.member,
            project="sde-consent-api",
            role=self.deployment_role.name,
        )

        projects.IAMMember(
            "project-cloudsql",
            member=self.sa.member,
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
            role_id=f"{self._format_role(self.config.stack)}_pushToGCR",
            title=f"{self.config.stack} push to GCR",
        )

        storage.BucketIAMBinding(
            "gcr-binding",
            bucket=storage.get_bucket("artifacts.sde-consent-api.appspot.com").name,
            members=[self.sa.member],
            role=access_to_storage_role.name,
        )

        self.workload_identity_provider = self.wi_provider.name
        pulumi.export("workload_identity_provider", self.wi_provider.name)

        self.service_account = self.sa.email
        pulumi.export("service_account", self.sa.email)

    def _format_role(self, role: str) -> str:
        return role.replace(".", "_").replace("/", "_").replace("-", "_")
