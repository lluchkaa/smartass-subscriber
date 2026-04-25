import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from smartass_subscriber.activities.calendar import fetch_sessions
from smartass_subscriber.activities.state import already_notified, mark_notified
from smartass_subscriber.activities.telegram import send_telegram_notification
from smartass_subscriber.config import get_settings
from smartass_subscriber.workflows.session_check import SessionCheckWorkflow


async def main() -> None:
    settings = get_settings()
    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)
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
