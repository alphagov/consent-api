from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from google.cloud import run_v2
from pulumi_gcp import cloudrun

from resources import AbstractResource
from resources.database import Database


class ProductionColor(Enum):
    GREEN = "green"
    BLUE = "blue"


_DEFAULT_PRODUCTION_INITIAL_TRAFFIC_PERCENT = 5


@dataclass(kw_only=True)
class CloudRun(AbstractResource):
    db: Database
    prod_initial_traffic_percent: int = _DEFAULT_PRODUCTION_INITIAL_TRAFFIC_PERCENT

    # Not in the constructor, for type hinting only
    next_color: ProductionColor | None = field(init=False, default=None)
    latest_color: ProductionColor | None = field(init=False, default=None)
    latest_rev_name: str | None = field(init=False, default=None)

    def _create(self):
        if self.config.env == "production":
            self.prepare_production()

        self.traffics = self.configure_traffics()

        self.service_name = self.resource_name("$-consent-api", self.config.stack)
        self.service = cloudrun.Service(
            self.config.name,
            name=self.service_name,
            location=self.config.region,
            template=self.make_template(),
            traffics=self.traffics,
        )

        # TODO only allow public access to production - other envs should be behind some
        # kind of auth
        cloudrun.IamBinding(
            self.resource_name("$--public-access-binding", self.config.name),
            location=self.service.location,
            service=self.service.name,
            role="roles/run.invoker",
            members=["allUsers"],
        )

    def make_template(self):
        return {
            "metadata": {
                "annotations": {
                    "autoscaling.knative.dev/maxScale": "5",
                    "run.googleapis.com/cloudsql-instances": self.db.connection_name,
                    "production-color": self.next_color.value
                    if self.next_color
                    else "none",
                }
            },
            "spec": {
                "containers": [
                    {
                        "image": f"gcr.io/{self.config.project_id}/consent-api:{self.config.tag}",  # noqa: E501
                        "envs": [
                            {"name": "DATABASE_URL", "value": self.db.db_url},
                            {"name": "ENV", "value": self.config.env},
                        ],
                    },
                ],
            },
        }

    def prepare_production(self):
        print("🚀 Deploying new Cloud Run revision to production")
        dot = {
            ProductionColor.GREEN: "🟢",
            ProductionColor.BLUE: "🔵",
        }
        latest_color, latest_rev_name = self.get_latest_production_revision()
        print(f"{dot[latest_color]} Latest color was {latest_color.value}")
        print(f"{dot[self.next_color]} Deploying to {self.next_color.value}")
        self.latest_color = latest_color
        self.latest_rev_name = latest_rev_name
        self.next_color = self.get_opposite_production_color(latest_color)

    def get_latest_production_revision(self) -> tuple[ProductionColor, str]:
        revclient = run_v2.RevisionsClient()
        service_name = "production-consent-api"
        parent = f"projects/{self.config.project_id}/locations/{self.config.region}/services/{service_name}"  # noqa: E501

        revisions = revclient.list_revisions(parent=parent)

        sorted_revs = sorted(
            revisions.revisions, key=lambda r: r.create_time, reverse=True
        )

        latest_rev = sorted_revs[0]
        try:
            col_annotation = latest_rev.annotations["production-color"]
            latest_color = ProductionColor(col_annotation)
        except ValueError as e:
            raise ValueError(
                f"Unknown color annotation on latest revision: {col_annotation}"
            ) from e

        return latest_color, latest_rev.name

    def configure_traffics(
        self,
    ) -> list[dict]:
        if self.config.env != "production":
            return [
                {
                    "latest_revision": True,
                    "percent": 100,
                },
            ]

        if not self.next_color:
            raise ValueError(
                "Production color must be specified for production env deployment"
            )
        prod_traffics = [
            {
                "latest_revision": True,
                "tag": self.next_color.value,
                "percent": 0,
            },
        ]

        if self.latest_color and self.latest_rev_name:
            prod_traffics[0]["percent"] = self.prod_initial_traffic_percent
            prod_traffics.append(
                {
                    "revision_name": self.latest_rev_name.split("/")[-1],
                    "tag": self.latest_color.value,
                    "percent": 100 - self.prod_initial_traffic_percent,
                }
            )

        print("🚀 Traffic configuration:")
        print(prod_traffics)

        return prod_traffics

    def get_opposite_production_color(self, color: ProductionColor) -> ProductionColor:
        """Get the opposite production color."""
        if color == ProductionColor.GREEN:
            return ProductionColor.BLUE
        return ProductionColor.GREEN
