from railway_sdk import database
from railway_sdk import define_railway
from railway_sdk import github
from railway_sdk import project
from railway_sdk import service
from railway_sdk import volume


@define_railway
def main(ctx=None):
    redis_db = database(
        "Redis",
        "redis",
        image="railwayapp/redis:7.2.5",
        region="us-west2",
    )
    redis_db = redis_db.with_fields(
        deploy={"multiRegionConfig": {"us-west2": {"numReplicas": 1}}},
    )
    postgres_db = database(
        "MHD-db",
        "postgres",
        image="ghcr.io/railwayapp-templates/postgres-ssl:latest",
        region="us-west2",
    )
    postgres_db = postgres_db.with_fields(
        deploy={"multiRegionConfig": {"us-west2": {"numReplicas": 1}}},
    )
    postgres_volume = volume(
        "Postgres-XMsW data",
        {
            "alerts": {"usage": {"100": {}, "80": {}, "95": {}}},
            "allowOnlineResize": True,
            "region": "us-west2",
            "sizeMB": 5000,
        },
    )
    redis_volume = volume(
        "redis data",
        {
            "alerts": {"usage": {"100": {}, "80": {}, "95": {}}},
            "allowOnlineResize": True,
            "region": "us-west2",
            "sizeMB": 5000,
        },
    )
    web = service(
        "MHD-web",
        source=github("abe-101/myHebrewDates", branch="main", checkSuites=True),
        build={
            "builder": "RAILPACK",
            "buildCommand": "python manage.py collectstatic --noinput && python manage.py compress --force",
        },
        start="gunicorn config.wsgi:application",
        preDeploy="python manage.py migrate",
        healthcheck="/ht/",
        deploy={"restartPolicyType": "ON_FAILURE", "restartPolicyMaxRetries": 10},
        replicas={"us-west2": 1},
        domains=["myhebrewdates.com"],
        networking={"privateNetworkEndpoint": "myhebrewdates"},
    )
    return project(
        "my_hebrew_dates",
        variables={"managed": False},
        resources=[redis_db, web, postgres_db, postgres_volume, redis_volume],
    )
