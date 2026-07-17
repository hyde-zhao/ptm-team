from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from trex_api.models import OperationEnvelope, success

OperationHandler = Callable[[dict[str, Any]], Awaitable[OperationEnvelope]]

SUPPORTED_OPS = {
    "tg_config_interface",
    "tg_apply_traffic_template",
    "tg_start_traffic_stream",
    "tg_verify_traffic_loss",
    "tg_stop_traffic_stream",
    "tg_delete_traffic_template",
}


async def mock_handler(op_id: str, payload: dict[str, Any]) -> OperationEnvelope:
    return success(op_id, {"accepted": True, "payload": payload})


def build_mock_registry() -> dict[str, OperationHandler]:
    return {
        op_id: (lambda payload, op_id=op_id: mock_handler(op_id, payload))
        for op_id in SUPPORTED_OPS
    }
