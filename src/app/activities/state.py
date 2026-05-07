import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from config import get_settings
from temporalio import activity

from app.models import NotificationState


def _state_path() -> Path:
    return Path(get_settings().state_file).expanduser()


def read_state() -> NotificationState | None:
    path = _state_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return NotificationState(
            last_notified=data["last_notified"],
            notified_at=data["notified_at"],
        )
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _write_state(state: NotificationState) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps({"last_notified": state.last_notified, "notified_at": state.notified_at})
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".smartass_state_")
    try:
        os.write(fd, data.encode())
        os.close(fd)
        os.replace(tmp, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        os.unlink(tmp)
        raise


@activity.defn
async def reset_state() -> None:
    path = _state_path()
    path.unlink(missing_ok=True)
    activity.logger.info("State reset: %s deleted", path)


@activity.defn
async def already_notified(date: str) -> bool:
    state = read_state()
    if state is None or state.last_notified != date:
        return False
    activity.logger.info("Already notified today (%s) at %s, skipping", date, state.notified_at)
    return True


@activity.defn
async def mark_notified(date: str) -> None:
    state = NotificationState(
        last_notified=date,
        notified_at=datetime.now(UTC).isoformat(),
    )
    _write_state(state)
    activity.logger.info("Marked notified for %s at %s", date, state.notified_at)
