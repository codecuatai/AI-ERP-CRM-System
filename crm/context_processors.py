import os


def crm_links(request):
    if os.environ.get("SUPERSET_PUBLIC_URL"):
        url = os.environ["SUPERSET_PUBLIC_URL"]
    else:
        host = request.get_host().split(":")[0] if request else "127.0.0.1"
        port = os.environ.get("SUPERSET_HOST_PORT", "18088")
        url = f"http://{host}:{port}"
    return {"superset_url": url.rstrip("/")}
