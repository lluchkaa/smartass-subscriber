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


async def _upsert_schedule(client: Client, schedule_id: str, schedule: Schedule) -> None:
    handle = client.get_schedule_handle(schedule_id)
    try:
        await handle.describe()
        await handle.update(lambda _: ScheduleUpdate(schedule=schedule))
        print(f"Schedule '{schedule_id}' updated")
    except RPCError:
        await client.create_schedule(schedule_id, schedule)
        print(f"Schedule '{schedule_id}' created")


async def ensure_schedule(client: Client, settings) -> None:
    await _upsert_schedule(
        client,
        "SmartassSessionCheck",
        Schedule(
            action=ScheduleActionStartWorkflow(
                SessionCheckWorkflow.run,
                id="SmartassSessionCheckWorkflow",
                task_queue=settings.temporal_task_queue,
            ),
            spec=ScheduleSpec(cron_expressions=["* 6-18 * * FRI"]),
            policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
            state=ScheduleState(
                note="Checks smartass.club for Monday sessions, notifies via Telegram"
            ),
        ),
    )
    await _upsert_schedule(
        client,
        "SmartassResetState",
        Schedule(
            action=ScheduleActionStartWorkflow(
                ResetStateWorkflow.run,
                id="SmartassResetStateWorkflow",
                task_queue=settings.temporal_task_queue,
            ),
            spec=ScheduleSpec(cron_expressions=["0 19 * * *"]),
            policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
            state=ScheduleState(note="Resets smartass state daily at midnight"),
        ),
    )


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
