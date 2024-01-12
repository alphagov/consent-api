from dataclasses import dataclass

import pulumi
from pulumi_gcp import compute

from resources import AbstractResource


@dataclass(kw_only=True)
class HTTPSLoadBalancer(AbstractResource):
    backend_service: compute.BackendService
    ip_address: compute.GlobalAddress

    def _create(self):
        https_path_matcher_name = self.resource_name(
            f"{self.config.stack}--$--https--path-matcher", self.config.name
        )
        https_paths = compute.URLMap(
            self.resource_name(
                f"{self.config.env}--$--https--load-balancer", self.config.name
            ),
            default_service=self.backend_service.id,
            host_rules=[
                compute.URLMapHostRuleArgs(
                    hosts=[pulumi.Config("sde-consent-api").require("domain")],
                    path_matcher=https_path_matcher_name,
                )
            ],
            path_matchers=[
                compute.URLMapPathMatcherArgs(
                    name=https_path_matcher_name,
                    default_service=self.backend_service.id,
                    path_rules=[
                        compute.URLMapPathMatcherPathRuleArgs(
                            paths=["/*"],
                            service=self.backend_service.id,
                        )
                    ],
                )
            ],
        )

        certificate = compute.ManagedSslCertificate(
            self.resource_name(f"{self.config.env}--$--certificate", self.config.name),
            managed=compute.ManagedSslCertificateManagedArgs(
                domains=[pulumi.Config("sde-consent-api").require("domain")],
            ),
        )

        https_proxy = compute.TargetHttpsProxy(
            resource_name=self.resource_name(
                f"{self.config.env}--$--https-proxy", self.config.name
            ),
            url_map=https_paths.id,
            ssl_certificates=[certificate.id],
        )

        compute.GlobalForwardingRule(
            resource_name=f"{self.config.env}--https--forwarding-rule",
            target=https_proxy.self_link,
            ip_address=self.ip_address.address,
            port_range="443",
            load_balancing_scheme="EXTERNAL",
        )
