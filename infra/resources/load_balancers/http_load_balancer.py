from dataclasses import dataclass

import pulumi
from pulumi_gcp import compute

from resources import AbstractResource


@dataclass(kw_only=True)
class HTTPLoadBalancer(AbstractResource):
    backend_service: compute.BackendService
    ip_address: compute.GlobalAddress

    def _create(self):
        http_path_matcher_name = f"{self.config.stack}--http--path-matcher"
        http_paths = compute.URLMap(
            f"{self.config.stack}--http--load-balancer",
            default_service=self.backend_service.id,
            host_rules=[
                compute.URLMapHostRuleArgs(
                    hosts=[pulumi.Config("sde-consent-api").require("domain")],
                    path_matcher=http_path_matcher_name,
                )
            ],
            path_matchers=[
                compute.URLMapPathMatcherArgs(
                    name=http_path_matcher_name,
                    default_service=self.backend_service.id,
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
            resource_name=f"{self.config.stack}--http-proxy",
            url_map=http_paths.id,
        )

        compute.GlobalForwardingRule(
            resource_name=f"{self.config.stack}--http-forwarding-rule",
            target=http_proxy.self_link,
            ip_address=self.ip_address.address,
            port_range="80",
            load_balancing_scheme="EXTERNAL",
        )
