from datetime import datetime

from prometheus_client import Gauge, start_http_server

from app.activities.state import read_state
from app.config import get_settings

notified_at_seconds = Gauge(
    "smartass_notified_at_seconds",
    "Unix timestamp of last session notification sent (one value per Friday)",
)


def init_metrics() -> None:
    settings = get_settings()
    state = read_state()
    if notified_at := state.get("notified_at"):
        try:
            ts = datetime.fromisoformat(notified_at).timestamp()
            notified_at_seconds.set(ts)
        except ValueError:
            pass

    start_http_server(settings.metrics_port)


def record_notification() -> None:
    notified_at_seconds.set_to_current_time()
