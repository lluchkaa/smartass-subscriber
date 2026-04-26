from telegram import Bot
from temporalio import activity

from app.config import get_settings


@activity.defn
async def send_telegram_notification(sessions: list[dict]) -> None:
    settings = get_settings()
    text = f"Smartass має заняття в наступний понеділок ({len(sessions)} сесій). Реєструйся!"

    bot = Bot(token=settings.telegram_bot_token)
    for chat_id in settings.telegram_user_ids:
        await bot.send_message(chat_id=chat_id, text=text)
    activity.logger.info(
        "Telegram notification sent (%d sessions, %d chats)",
        len(sessions),
        len(settings.telegram_user_ids),
    )
