from dataclasses import dataclass

from pulumi_gcp import compute

from resources import AbstractResource
from resources.cloudrun import CloudRun
from resources.load_balancers.http_load_balancer import HTTPLoadBalancer
from resources.load_balancers.https_load_balancer import HTTPSLoadBalancer


@dataclass(kw_only=True)
class LoadBalancers(AbstractResource):
    cloud_run: CloudRun

    def _create(self):
        self.ip_address = compute.GlobalAddress(
            self.resource_name(f"{self.config.stack}--$--ipaddress", self.config.stack),
            address_type="EXTERNAL",
            project=self.config.project_id,
        )

        self.endpoint_group = compute.RegionNetworkEndpointGroup(
            self.resource_name(
                f"{self.config.stack}--$--endpoint-group", self.config.stack
            ),
            network_endpoint_type="SERVERLESS",
            region=self.config.region,
            cloud_run=compute.RegionNetworkEndpointGroupCloudRunArgs(
                service=self.cloud_run.service_name
            ),
        )

        self.default_rule = compute.SecurityPolicyRuleArgs(
            priority=2147483647,
            action="allow",
            match=compute.SecurityPolicyRuleMatchArgs(
                versioned_expr="SRC_IPS_V1",
                config=compute.SecurityPolicyRuleMatchConfigArgs(src_ip_ranges=["*"]),
            ),
        )

        self.rate_limiting_rule = compute.SecurityPolicyRuleArgs(
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

        self.security_rules = [self.default_rule, self.rate_limiting_rule]

        self.security_policy = compute.SecurityPolicy(
            resource_name=self.resource_name(
                f"{self.config.stack}--$--security-policy", self.config.stack
            ),
            rules=self.security_rules,
        )

        self.backend_service = compute.BackendService(
            self.resource_name(
                f"{self.config.stack}--$--backend-service", self.config.stack
            ),
            enable_cdn=False,
            connection_draining_timeout_sec=10,
            log_config=compute.BackendServiceLogConfigArgs(
                enable=True, sample_rate=0.5
            ),
            backends=[compute.BackendServiceBackendArgs(group=self.endpoint_group.id)],
            security_policy=self.security_policy.self_link,
        )

        self.https_load_balancer = HTTPSLoadBalancer(
            config=self.config,
            backend_service=self.backend_service,
            ip_address=self.ip_address,
        )
        self.http_load_balancer = HTTPLoadBalancer(
            config=self.config,
            backend_service=self.backend_service,
            ip_address=self.ip_address,
        )
