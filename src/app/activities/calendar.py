import httpx
from bs4 import BeautifulSoup
from config import get_settings
from temporalio import activity

from app.models import Session


def parse_sessions(html: str, target_date: str) -> list[Session]:
    soup = BeautifulSoup(html, "lxml")
    date_pane = soup.find(id=f"date-{target_date}")
    if date_pane is None:
        return []

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
    return sessions


@activity.defn
async def fetch_sessions(target_date: str) -> list[Session]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(settings.smartass_url)
        response.raise_for_status()

    sessions = parse_sessions(response.text, target_date)
    if not sessions:
        activity.logger.warning(
            "No sessions found for %s — date pane missing or scraper broken", target_date
        )
    else:
        activity.logger.info("Found %d sessions on %s", len(sessions), target_date)
    return sessions
