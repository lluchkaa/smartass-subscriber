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

from smartass_subscriber.config import get_settings
from smartass_subscriber.workflows.session_check import SessionCheckWorkflow

SCHEDULE_ID = "smartass-session-check"
# Every minute, 9:00–21:59, on Fridays (last trigger fires at 21:00)
CRON_SPEC = "* 9-21 * * FRI"


async def main() -> None:
    settings = get_settings()
    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)

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
        print(f"Updated schedule '{SCHEDULE_ID}'")
    except RPCError:
        await client.create_schedule(SCHEDULE_ID, schedule)
        print(f"Created schedule '{SCHEDULE_ID}'")

    print(f"Cron:      {CRON_SPEC}")
    print(f"Namespace: {settings.temporal_namespace}")
    print(f"Queue:     {settings.temporal_task_queue}")


if __name__ == "__main__":
    asyncio.run(main())
