ALLOWED_SERVICES = {
    "payment-service",
    "user-service",
}

deployments = [
    {
        "service": "payment-service",
        "status": "deployed",
        "version": "v1.4.2",
    },
    {
        "service": "user-service",
        "status": "in_progress",
        "version": "v2.1.0",
    },
]

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
    if service is not None and service not in ALLOWED_SERVICES:
        raise ValueError(
            f"Unsupported service: {service}"
        )
    failed_builds = []

    for build in builds:
        if build["status"] == "failed":
            if service is None or build["service"] == service:
              failed_builds.append(build)

    return failed_builds

def get_deploy_status(service):
    """Return the deployment status for a supported service."""
    
    if service not in ALLOWED_SERVICES:
        raise ValueError(f"Unsupported service: {service}")
     
    for deployment in deployments:
        if deployment["service"] == service:
            return deployment
        
    return None
