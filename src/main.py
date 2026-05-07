import asyncio

from config import get_settings
from temporal.namespace import ensure_namespace
from temporal.worker import ensure_schedule, run_worker
from temporalio.client import Client


async def main() -> None:
    settings = get_settings()
    bootstrap = await Client.connect(settings.temporal_host, namespace="default")
    await ensure_namespace(bootstrap, settings.temporal_namespace)
    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)
    await ensure_schedule(client, settings)
    await run_worker(client, settings)


if __name__ == "__main__":
    asyncio.run(main())
