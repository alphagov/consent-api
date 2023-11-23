from enum import Enum

from google.cloud import run_v2

PRODUCTION_INITIAL_TRAFFIC_PERCENT = 5


class ProductionColor(Enum):
    GREEN = "green"
    BLUE = "blue"


def get_latest_production_revision(
    project_id: str, region: str, service_name: str
) -> tuple[ProductionColor, str]:
    revclient = run_v2.RevisionsClient()
    service_name = "production-consent-api"
    parent = f"projects/{project_id}/locations/{region}/services/{service_name}"

    revisions = revclient.list_revisions(parent=parent)

    sorted_revs = sorted(revisions.revisions, key=lambda r: r.create_time, reverse=True)

    latest_rev = sorted_revs[0]
    try:
        col_annotation = latest_rev.annotations["production-color"]
        latest_color = ProductionColor(col_annotation)
    except ValueError as e:
        raise ValueError(
            f"Unknown color annotation on latest revision: {col_annotation}"
        ) from e

    return latest_color, latest_rev.name


def get_opposite_production_color(color: ProductionColor) -> ProductionColor:
    """Get the opposite production color."""
    if color == ProductionColor.GREEN:
        return ProductionColor.BLUE
    return ProductionColor.GREEN


def configure_cloud_run_traffics(
    env: str,
    next_production_color: ProductionColor | None,
    latest_color: ProductionColor | None,
    latest_rev_name: str | None,
) -> list[dict]:
    if env != "production":
        return [
            {
                "latest_revision": True,
                "percent": 100,
            },
        ]

    if not next_production_color:
        raise ValueError(
            "Production color must be specified for production env deployment"
        )
    prod_traffics = [
        {
            "latest_revision": True,
            "tag": next_production_color.value,
            "percent": 0,
        },
    ]

    if latest_color and latest_rev_name:
        prod_traffics[0]["percent"] = PRODUCTION_INITIAL_TRAFFIC_PERCENT
        prod_traffics.append(
            {
                "revision_name": latest_rev_name.split("/")[-1],
                "tag": latest_color.value,
                "percent": 100 - PRODUCTION_INITIAL_TRAFFIC_PERCENT,
            }
        )

    print("🚀 Traffic configuration:")
    print(prod_traffics)

    return prod_traffics
