import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from temporalio import activity

from app.config import get_settings


def _state_path() -> Path:
    return Path(get_settings().state_file).expanduser()


def read_state() -> dict:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


@activity.defn
async def already_notified(date: str) -> bool:
    state = read_state()
    if state.get("last_notified") != date:
        return False
    notified_at = state.get("notified_at", "unknown time")
    activity.logger.info("Already notified today (%s) at %s, skipping", date, notified_at)
    return True


@activity.defn
async def mark_notified(date: str) -> None:
    notified_at = datetime.now(UTC).isoformat()
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps({"last_notified": date, "notified_at": notified_at})
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".smartass_state_")
    try:
        os.write(fd, data.encode())
        os.close(fd)
        os.replace(tmp, path)
    except Exception:
        os.close(fd)
        os.unlink(tmp)
        raise
    from app.metrics import record_notification

    record_notification()
    activity.logger.info("Marked notified for %s at %s", date, notified_at)
