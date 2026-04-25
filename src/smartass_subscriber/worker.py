import asyncio

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleState,
    ScheduleUpdate,
)
from temporalio.common import WorkflowIDReusePolicy
from temporalio.service import RPCError
from temporalio.worker import Worker

from smartass_subscriber.activities.calendar import fetch_sessions
from smartass_subscriber.activities.state import already_notified, mark_notified
from smartass_subscriber.activities.telegram import send_telegram_notification
from smartass_subscriber.config import get_settings
from smartass_subscriber.workflows.session_check import SessionCheckWorkflow

SCHEDULE_ID = "smartass-session-check"
CRON_SPEC = "* 9-21 * * FRI"


async def ensure_schedule(client: Client, settings) -> None:
    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            SessionCheckWorkflow.run,
            id="smartass-session-check-workflow",
            task_queue=settings.temporal_task_queue,
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        ),
        spec=ScheduleSpec(cron_expressions=[CRON_SPEC]),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
        state=ScheduleState(note="Checks smartass.club for Monday sessions, notifies via Telegram"),
    )

    handle = client.get_schedule_handle(SCHEDULE_ID)
    try:
        await handle.describe()
        await handle.update(lambda _: ScheduleUpdate(schedule=schedule))
        print(f"Schedule '{SCHEDULE_ID}' updated")
    except RPCError:
        await client.create_schedule(SCHEDULE_ID, schedule)
        print(f"Schedule '{SCHEDULE_ID}' created")


async def main() -> None:
    settings = get_settings()
    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)

    await ensure_schedule(client, settings)

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[SessionCheckWorkflow],
        activities=[fetch_sessions, already_notified, mark_notified, send_telegram_notification],
    )
    print(
        f"Worker started on task queue '{settings.temporal_task_queue}'"
        f" (namespace: {settings.temporal_namespace})"
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
