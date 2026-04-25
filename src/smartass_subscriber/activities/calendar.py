import httpx
from bs4 import BeautifulSoup
from temporalio import activity

from smartass_subscriber.config import get_settings


@activity.defn
async def fetch_sessions(target_date: str) -> list[dict]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(settings.smartass_url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    date_pane = soup.find(id=f"date-{target_date}")

    if date_pane is None:
        activity.logger.warning(
            "Date pane not found for %s — page may not cover that week", target_date
        )
        return []

    sessions = []
    for event in date_pane.find_all("a", class_="scheduler_event"):
        name_el = event.find(class_="calenar-training-title")
        time_el = event.find(class_="calenar-training-duration")
        trainer_el = event.find(class_="calenar-training-trainer")

        name = name_el.get_text(separator=" ", strip=True) if name_el else ""
        time = time_el.get_text(strip=True) if time_el else ""
        trainer = trainer_el.get_text(strip=True) if trainer_el else ""

        sessions.append({"name": name, "time": time, "instructor": trainer})

    activity.logger.info("Found %d sessions on %s", len(sessions), target_date)
    return sessions
