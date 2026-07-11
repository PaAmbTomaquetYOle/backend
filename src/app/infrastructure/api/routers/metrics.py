"""Prometheus scrape endpoint, gated by Settings.metrics_enabled (BE-20).

Kept as a plain top-level function like `health.py`'s `/health` — a
single-line handler forwarding to `prometheus_client` doesn't warrant its own
class, and following `health.py`'s existing shape keeps routers consistent.
"""

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    """Expose handled-failure counters in the Prometheus text exposition format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
