from app.reset_state.activities import reset_state
from app.reset_state.workflow import ResetStateWorkflow
from app.session_check.activities import (
    already_notified,
    fetch_sessions,
    get_target_sessions,
    mark_notified,
    send_telegram_notification,
)
from app.session_check.workflow import SessionCheckWorkflow
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
from temporalio.service import RPCError
from temporalio.worker import Worker

SCHEDULE_ID = "SmartassSessionCheck"
CRON_SPEC = "* 9-21 * * FRI"


def _build_schedule(settings) -> Schedule:
    return Schedule(
        action=ScheduleActionStartWorkflow(
            SessionCheckWorkflow.run,
            id="SmartassSessionCheckWorkflow",
            task_queue=settings.temporal_task_queue,
        ),
        spec=ScheduleSpec(cron_expressions=[CRON_SPEC]),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
        state=ScheduleState(note="Checks smartass.club for Monday sessions, notifies via Telegram"),
    )


async def ensure_schedule(client: Client, settings) -> None:
    schedule = _build_schedule(settings)
    handle = client.get_schedule_handle(SCHEDULE_ID)
    try:
        await handle.describe()
        await handle.update(lambda _: ScheduleUpdate(schedule=schedule))
        print(f"Schedule '{SCHEDULE_ID}' updated")
    except RPCError:
        await client.create_schedule(SCHEDULE_ID, schedule)
        print(f"Schedule '{SCHEDULE_ID}' created")


async def run_worker(client: Client, settings) -> None:
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[SessionCheckWorkflow, ResetStateWorkflow],
        activities=[
            already_notified,
            fetch_sessions,
            get_target_sessions,
            send_telegram_notification,
            mark_notified,
            reset_state,
        ],
    )
    print(
        f"Worker started on task queue '{settings.temporal_task_queue}'"
        f" (namespace: {settings.temporal_namespace})"
    )
    await worker.run()
