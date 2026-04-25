from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.activities.calendar import fetch_sessions
    from app.activities.state import already_notified, mark_notified
    from app.activities.telegram import send_telegram_notification


@workflow.defn
class SessionCheckWorkflow:
    @workflow.run
    async def run(self) -> None:
        today = workflow.now()
        today_str = today.strftime("%Y-%m-%d")

        notified = await workflow.execute_activity(
            already_notified,
            today_str,
            start_to_close_timeout=timedelta(seconds=10),
        )
        if notified:
            workflow.logger.info("Already notified today (%s), skipping", today_str)
            return

        # From Friday (weekday=4): next Monday = +3 days, Monday after next = +10 days
        days_to_next_monday = (7 - today.weekday()) % 7 or 7
        target = today + timedelta(days=days_to_next_monday + 7)
        target_date = target.strftime("%Y-%m-%d")
        workflow.logger.info("Checking sessions for %s", target_date)

        sessions = await workflow.execute_activity(
            fetch_sessions,
            target_date,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not sessions:
            workflow.logger.info("No sessions on %s", target_date)
            return

        await workflow.execute_activity(
            send_telegram_notification,
            sessions,
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            mark_notified,
            today_str,
            start_to_close_timeout=timedelta(seconds=10),
        )
