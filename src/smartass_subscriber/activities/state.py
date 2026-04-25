import json
import os
import tempfile
from pathlib import Path

from temporalio import activity

from smartass_subscriber.config import get_settings


def _state_path() -> Path:
    return Path(get_settings().state_file).expanduser()


@activity.defn
async def already_notified(date: str) -> bool:
    path = _state_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
        return data.get("last_notified") == date
    except (json.JSONDecodeError, OSError):
        return False


@activity.defn
async def mark_notified(date: str) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps({"last_notified": date})
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".smartass_state_")
    try:
        os.write(fd, data.encode())
        os.close(fd)
        os.replace(tmp, path)
    except Exception:
        os.close(fd)
        os.unlink(tmp)
        raise
    activity.logger.info("Marked notified for %s", date)
