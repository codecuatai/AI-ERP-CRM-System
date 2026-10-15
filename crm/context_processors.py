import os


def crm_links(request):
    url = os.environ.get("SUPERSET_PUBLIC_URL") or "http://127.0.0.1:" + os.environ.get("SUPERSET_HOST_PORT", "18088")
    return {"superset_url": url.rstrip("/")}
