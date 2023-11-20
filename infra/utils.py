from google.cloud import run_v2
from enum import Enum


class ProductionColor(Enum):
    GREEN = "green"
    BLUE = "blue"


def get_latest_production_color() -> ProductionColor:
    client = run_v2.ServicesClient()
    PROJECT_ID = "sde-consent-api"
    REGION = "europe-west2"

    service_name = "production-consent-api"
    parent = f"projects/{PROJECT_ID}/locations/{REGION}/services/{service_name}"

    service = client.get_service(name=parent)

    for ts in service.traffic_statuses:
        if (
            ts.type_
            == run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST
        ):
            try:
                return ProductionColor(ts.tag.lower())
            except:
                raise Exception(f"Unknown tag for latest revision: {ts.tag}")

    raise Exception("No latest revision found")


def get_opposite_production_color(color: ProductionColor) -> ProductionColor:
    """Get the opposite production color."""
    if color == ProductionColor.GREEN:
        return ProductionColor.BLUE
    return ProductionColor.GREEN
