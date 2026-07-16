from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OperationStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class ErrorType(str, Enum):
    NONE = "NONE"
    INVALID_PARAM = "INVALID_PARAM"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DEVICE_UNREACHABLE = "DEVICE_UNREACHABLE"
    STATE_MISMATCH = "STATE_MISMATCH"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class OperationEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op_id: str
    status: OperationStatus
    data: dict[str, Any] = Field(default_factory=dict)
    error_type: ErrorType = ErrorType.NONE
    diag_snapshot_ref: str = ""


def success(op_id: str, data: dict[str, Any] | None = None) -> OperationEnvelope:
    return OperationEnvelope(
        op_id=op_id,
        status=OperationStatus.SUCCESS,
        data=data or {},
        error_type=ErrorType.NONE,
        diag_snapshot_ref="",
    )


def failed(
    op_id: str,
    error_type: ErrorType,
    data: dict[str, Any] | None = None,
    diag_snapshot_ref: str = "",
) -> OperationEnvelope:
    return OperationEnvelope(
        op_id=op_id,
        status=OperationStatus.FAILED,
        data=data or {},
        error_type=error_type,
        diag_snapshot_ref=diag_snapshot_ref,
    )
