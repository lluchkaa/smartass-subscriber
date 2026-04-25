from telegram import Bot
from temporalio import activity

from smartass_subscriber.config import get_settings


@activity.defn
async def send_telegram_notification(sessions: list[dict]) -> None:
    settings = get_settings()
    lines = ["<b>Smartass sessions next Monday:</b>"]
    for s in sessions:
        lines.append(f"• <b>{s['name']}</b> — {s['time']} ({s['instructor']})")
    text = "\n".join(lines)

    bot = Bot(token=settings.telegram_bot_token)
    await bot.send_message(chat_id=settings.telegram_chat_id, text=text, parse_mode="HTML")
    activity.logger.info("Telegram notification sent (%d sessions)", len(sessions))
