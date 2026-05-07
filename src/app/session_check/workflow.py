from datetime import timedelta

from temporalio import workflow

from app.shared.dates import target_week

with workflow.unsafe.imports_passed_through():
    from app.session_check.activities import (
        already_notified,
        fetch_sessions,
        get_target_sessions,
        mark_notified,
        send_telegram_notification,
    )


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

        target_dates = [d.strftime("%Y-%m-%d") for d in target_week(today.date())]
        workflow.logger.info("Checking sessions for %s", target_dates)

        all_sessions = await workflow.execute_activity(
            fetch_sessions,
            start_to_close_timeout=timedelta(seconds=30),
        )

        target_sessions = await workflow.execute_activity(
            get_target_sessions,
            (all_sessions, target_dates),
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not target_sessions:
            workflow.logger.info("No target dates found on page: %s", target_dates)
            return

        await workflow.execute_activity(
            send_telegram_notification,
            target_sessions,
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            mark_notified,
            today_str,
            start_to_close_timeout=timedelta(seconds=10),
        )
