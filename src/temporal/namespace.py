from datetime import timedelta

from google.protobuf.duration_pb2 import Duration
from temporalio.api.workflowservice.v1 import DescribeNamespaceRequest, RegisterNamespaceRequest
from temporalio.client import Client
from temporalio.service import RPCError


async def ensure_namespace(client: Client, namespace: str) -> None:
    try:
        await client.workflow_service.describe_namespace(
            DescribeNamespaceRequest(namespace=namespace)
        )
    except RPCError:
        await client.workflow_service.register_namespace(
            RegisterNamespaceRequest(
                namespace=namespace,
                workflow_execution_retention_period=Duration(
                    seconds=int(timedelta(days=7).total_seconds())
                ),
            )
        )
        print(f"Namespace '{namespace}' created")
