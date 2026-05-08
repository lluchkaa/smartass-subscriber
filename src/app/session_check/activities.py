import httpx
from bs4 import BeautifulSoup
from config import get_settings
from telegram import Bot
from temporalio import activity

from app.shared.models import Session
from app.shared.state import already_notified, mark_notified

__all__ = [
    "fetch_sessions",
    "get_target_sessions",
    "send_telegram_notification",
    "already_notified",
    "mark_notified",
]


def parse_sessions(html: str) -> dict[str, list[Session]]:
    soup = BeautifulSoup(html, "lxml")
    result: dict[str, list[Session]] = {}
    for date_pane in soup.find_all(id=lambda x: bool(x and x.startswith("date-"))):
        pane_id = date_pane["id"]
        date_str = (pane_id if isinstance(pane_id, str) else pane_id[0])[len("date-") :]
        sessions = []
        for event in date_pane.find_all("a", class_="scheduler_event"):
            name_el = event.find(class_="calenar-training-title")
            time_el = event.find(class_="calenar-training-duration")
            trainer_el = event.find(class_="calenar-training-trainer")
            sessions.append(
                Session(
                    name=name_el.get_text(separator=" ", strip=True) if name_el else "",
                    time=time_el.get_text(strip=True) if time_el else "",
                    instructor=trainer_el.get_text(strip=True) if trainer_el else "",
                )
            )
        result[date_str] = sessions
    return result


@activity.defn
async def fetch_sessions() -> dict[str, list[Session]]:
    settings = get_settings()
    headers = {"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(settings.smartass_url, headers=headers)
        response.raise_for_status()

    all_sessions = parse_sessions(response.text)
    activity.logger.info("Found %d date panes on page", len(all_sessions))
    return all_sessions


@activity.defn
async def get_target_sessions(
    args: tuple[dict[str, list[Session]], list[str]],
) -> dict[str, list[Session]]:
    all_sessions, target_dates = args
    target = {date: all_sessions[date] for date in target_dates if all_sessions.get(date)}
    if not target:
        activity.logger.warning("None of the target dates %s found on page", target_dates)
    else:
        activity.logger.info("Found %d target date(s) on page: %s", len(target), list(target))
    return target


@activity.defn
async def send_telegram_notification(sessions: dict[str, list[Session]]) -> None:
    settings = get_settings()
    total = sum(len(s) for s in sessions.values())
    days = ", ".join(sorted(sessions))
    text = f"Smartass має заняття ({days}, {total} сесій). Реєструйся!"

    bot = Bot(token=settings.telegram_bot_token)
    for chat_id in settings.telegram_user_ids:
        await bot.send_message(chat_id=chat_id, text=text)
    activity.logger.info(
        "Telegram notification sent (%d sessions across %d days, %d chats)",
        total,
        len(sessions),
        len(settings.telegram_user_ids),
    )
