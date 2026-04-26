from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.activities.state import reset_state


@workflow.defn
class ResetStateWorkflow:
    @workflow.run
    async def run(self) -> None:
        await workflow.execute_activity(
            reset_state,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("State reset complete")
