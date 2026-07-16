from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

from trex_api.models import ErrorType
from trex_api.ops.registry import OperationHandler
from trex_api.service import TrexOperationService, build_service_registry


def create_app(registry: dict[str, OperationHandler] | None = None) -> FastAPI:
    app = FastAPI(title="TRex Atomic Operation API", version="0.0.0")
    app.state.registry = registry or build_service_registry(TrexOperationService())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/ops/{op_id}")
    async def run_operation(op_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        handler = app.state.registry.get(op_id)
        if handler is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_type": ErrorType.INVALID_PARAM,
                    "message": f"unsupported op_id: {op_id}",
                },
            )
        envelope = await handler(payload)
        return envelope.model_dump(mode="json")

    return app


app = create_app()


def main() -> None:
    uvicorn.run("trex_api.api:app", host="0.0.0.0", port=8000)
