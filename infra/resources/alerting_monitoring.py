from dataclasses import dataclass
from dataclasses import field

from pulumi_gcp import monitoring

from resources import AbstractResource
from resources.cloudrun import CloudRun


@dataclass(kw_only=True)
class AlertingMonitoring(AbstractResource):
    cloud_run: CloudRun

    # Not in the constructor, for type hinting only
    email_notification_channel: monitoring.NotificationChannel | None = field(
        init=False, default=None
    )
    notification_channels: list[monitoring.NotificationChannel] | None = field(
        init=False, default=None
    )
    alert_4xx: monitoring.AlertPolicy | None = field(init=False, default=None)
    alert_5xx: monitoring.AlertPolicy | None = field(init=False, default=None)
    alert_py_exception: monitoring.AlertPolicy | None = field(init=False, default=None)
    alerts: list[monitoring.AlertPolicy] | None = field(init=False, default=None)

    def _create(self):
        self.create_notification_channels()
        self.create_log_based_alerts()

    def create_notification_channels(self):
        self.notification_channels = []
        self.email_notification_channel = monitoring.NotificationChannel(
            resource_name=f"single-consent-email-alerts-{self.config.stack}",
            display_name=f"Single Consent Email Alerts {self.config.stack}",
            description="Alerts for single consent via emails",
            type="email",
            labels={"email_address": "data-tools-alerts@digital.cabinet-office.gov.uk"},
        )
        self.notification_channels.append(self.email_notification_channel)

    def create_log_based_alerts(self):
        self.create_4xx_alert()
        self.create_5xx_alert()
        self.create_python_exception_alert()

    def create_4xx_alert(self):
        self.alerts = []
        self.alert_4xx = monitoring.AlertPolicy(
            resource_name=f"{self.config.stack} HTTP 4XX Errors",
            display_name=f"{self.config.stack} HTTP 4XX Errors",
            conditions=[
                monitoring.AlertPolicyConditionArgs(
                    display_name="Log match condition: 4XX HTTP error Test",
                    condition_matched_log=monitoring.AlertPolicyConditionConditionMatchedLogArgs(
                        filter=(
                            'resource.type = "cloud_run_revision" '
                            f'resource.labels.service_name = "{self.cloud_run.service_name}" '  # noqa: E501
                            'resource.labels.location = "europe-west2" '
                            "httpRequest.status>=400 "
                            "httpRequest.status < 500"
                        ),
                    ),
                )
            ],
            combiner="OR",
            alert_strategy=monitoring.AlertPolicyAlertStrategyArgs(
                notification_rate_limit=monitoring.AlertPolicyAlertStrategyNotificationRateLimitArgs(
                    period=f"{str(60 * 5)}s"
                ),
            ),
            notification_channels=[self.email_notification_channel.name],
        )
        self.alerts.append(self.alert_4xx)

    def create_5xx_alert(self):
        self.alert_5xx = monitoring.AlertPolicy(
            resource_name=f"{self.config.stack} HTTP 5XX Errors",
            display_name=f"{self.config.stack} HTTP 5XX Errors",
            conditions=[
                monitoring.AlertPolicyConditionArgs(
                    display_name="Log match condition: 5XX HTTP error Test",
                    condition_matched_log=monitoring.AlertPolicyConditionConditionMatchedLogArgs(
                        filter=(
                            'resource.type = "cloud_run_revision" '
                            f'resource.labels.service_name = "{self.cloud_run.service_name}" '  # noqa: E501
                            'resource.labels.location = "europe-west2" '
                            "httpRequest.status>=500"
                        ),
                    ),
                )
            ],
            combiner="OR",
            alert_strategy=monitoring.AlertPolicyAlertStrategyArgs(
                notification_rate_limit=monitoring.AlertPolicyAlertStrategyNotificationRateLimitArgs(
                    period=f"{str(60 * 5)}s"
                ),
            ),
            notification_channels=[self.email_notification_channel.name],
        )
        self.alerts.append(self.alert_5xx)

    def create_python_exception_alert(self):
        self.alert_py_exception = monitoring.AlertPolicy(
            resource_name=f"{self.config.stack} Python API Exceptions",
            display_name=f"{self.config.stack} Python API Exceptions",
            conditions=[
                monitoring.AlertPolicyConditionArgs(
                    display_name="Log match condition: any Python API exception with a traceback",  # noqa: E501
                    condition_matched_log=monitoring.AlertPolicyConditionConditionMatchedLogArgs(
                        filter=('severity=ERROR textPayload=~"^Traceback"'),
                    ),
                )
            ],
            combiner="OR",
            alert_strategy=monitoring.AlertPolicyAlertStrategyArgs(
                notification_rate_limit=monitoring.AlertPolicyAlertStrategyNotificationRateLimitArgs(
                    period=f"{str(60 * 5)}s"
                ),
            ),
            notification_channels=[self.email_notification_channel.name],
        )
        self.alerts.append(self.alert_py_exception)
