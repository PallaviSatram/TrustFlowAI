
# Sample build data for our TrustFlow AI project
builds = [
    {
        "build_id": 101,
        "service": "payment-service",
        "status": "failed",
        "error": "Database connection timeout"
    },
    {
        "build_id": 102,
        "service": "user-service",
        "status": "success",
        "error": None
    },
    {
        "build_id": 103,
        "service": "payment-service",
        "status": "failed",
        "error": "Unit tests failed"
    }
]


def list_failed_builds(service = None):
    """Return failed builds, optionally filtered by service."""
    failed_builds = []

    for build in builds:
        if build["status"] == "failed":
            if service is None or build["service"] == service:
              failed_builds.append(build)

    return failed_builds
