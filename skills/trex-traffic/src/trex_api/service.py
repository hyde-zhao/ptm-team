from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from trex_api.models import ErrorType, OperationEnvelope, failed, success
from trex_api.runtime import RuntimeStore
from trex_api.schemas import (
    ApplyTrafficTemplateRequest,
    ConfigInterfaceRequest,
    DeleteTrafficTemplateRequest,
    StartTrafficStreamRequest,
    StopTrafficStreamRequest,
    VerifyTrafficLossRequest,
)
from trex_api.settings import Settings, load_settings
from trex_api.trex.api_client import SimulatedTrexClient, TrexClient, TrexPythonApiClient
from trex_api.trex.stats_parser import compute_loss, extract_port_packets
from trex_api.trex.template_renderer import write_template_yaml


class TrexOperationService:
    def __init__(
        self,
        settings: Settings | None = None,
        client: TrexClient | None = None,
        store: RuntimeStore | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.client = client or _build_client(self.settings.backend)
        self.store = store or RuntimeStore()

    async def config_interface(self, payload: dict[str, Any]) -> OperationEnvelope:
        try:
            request = ConfigInterfaceRequest.model_validate(payload)
            interfaces = self.client.configure_interfaces(request.interfaces)
        except ValidationError as exc:
            return failed("tg_config_interface", ErrorType.INVALID_PARAM, {"errors": exc.errors()})
        except Exception as exc:
            return failed("tg_config_interface", ErrorType.INTERNAL_ERROR, {"message": str(exc)})

        failed_neighbors = [item for item in interfaces if not item.get("neighbor_learned")]
        if failed_neighbors:
            return failed(
                "tg_config_interface",
                ErrorType.STATE_MISMATCH,
                {
                    "interfaces": interfaces,
                    "failed_ports": [item.get("port") for item in failed_neighbors],
                },
            )
        return success("tg_config_interface", {"interfaces": interfaces, "status": "configured"})

    async def apply_traffic_template(self, payload: dict[str, Any]) -> OperationEnvelope:
        try:
            request = ApplyTrafficTemplateRequest.model_validate(payload)
            path = write_template_yaml(self.settings.template_dir, request)
        except ValidationError as exc:
            return failed("tg_apply_traffic_template", ErrorType.INVALID_PARAM, {"errors": exc.errors()})
        except Exception as exc:
            return failed("tg_apply_traffic_template", ErrorType.INTERNAL_ERROR, {"message": str(exc)})

        self.store.templates[request.template] = path
        return success(
            "tg_apply_traffic_template",
            {
                "template": request.template,
                "template_path": str(path),
                "status": "applied",
                "updated": True,
            },
        )

    async def start_traffic_stream(self, payload: dict[str, Any]) -> OperationEnvelope:
        try:
            request = StartTrafficStreamRequest.model_validate(payload)
        except ValidationError as exc:
            return failed("tg_start_traffic_stream", ErrorType.INVALID_PARAM, {"errors": exc.errors()})

        template_path = self._template_path(request.template)
        if template_path is None:
            return failed(
                "tg_start_traffic_stream",
                ErrorType.RESOURCE_NOT_FOUND,
                {"template": request.template},
            )

        try:
            data = self.client.start_stream(request, template_path)
        except Exception as exc:
            return failed("tg_start_traffic_stream", ErrorType.INTERNAL_ERROR, {"message": str(exc)})

        self.store.streams[request.name] = data
        return success("tg_start_traffic_stream", data)

    async def verify_traffic_loss(self, payload: dict[str, Any]) -> OperationEnvelope:
        try:
            request = VerifyTrafficLossRequest.model_validate(payload)
        except ValidationError as exc:
            return failed("tg_verify_traffic_loss", ErrorType.INVALID_PARAM, {"errors": exc.errors()})

        if request.name not in self.store.streams:
            return failed("tg_verify_traffic_loss", ErrorType.RESOURCE_NOT_FOUND, {"name": request.name})

        if self.settings.verify_sample_seconds > 0:
            await asyncio.sleep(self.settings.verify_sample_seconds)

        try:
            stats = self.client.get_port_stats(request.ports)
            tx_packets, rx_packets = extract_port_packets(stats, request.txport, request.rxport)
        except Exception as exc:
            return failed("tg_verify_traffic_loss", ErrorType.INTERNAL_ERROR, {"message": str(exc)})

        loss, loss_ratio = compute_loss(tx_packets, rx_packets)
        data = {
            "passed": loss_ratio <= request.max_loss,
            "tx_packets": tx_packets,
            "rx_packets": rx_packets,
            "loss": loss,
            "loss_ratio": loss_ratio,
            "max_loss": request.max_loss,
        }
        if tx_packets <= 0:
            data["passed"] = False
            data["reason"] = "no transmitted packets were observed"
            return failed("tg_verify_traffic_loss", ErrorType.STATE_MISMATCH, data)
        if data["passed"]:
            return success("tg_verify_traffic_loss", data)
        return failed("tg_verify_traffic_loss", ErrorType.STATE_MISMATCH, data)

    async def stop_traffic_stream(self, payload: dict[str, Any]) -> OperationEnvelope:
        try:
            request = StopTrafficStreamRequest.model_validate(payload)
        except ValidationError as exc:
            return failed("tg_stop_traffic_stream", ErrorType.INVALID_PARAM, {"errors": exc.errors()})

        if request.name not in self.store.streams:
            return failed("tg_stop_traffic_stream", ErrorType.RESOURCE_NOT_FOUND, {"name": request.name})

        try:
            data = self.client.stop_stream(request)
        except Exception as exc:
            return failed("tg_stop_traffic_stream", ErrorType.INTERNAL_ERROR, {"message": str(exc)})

        self.store.streams.pop(request.name, None)
        return success("tg_stop_traffic_stream", data)

    async def delete_traffic_template(self, payload: dict[str, Any]) -> OperationEnvelope:
        try:
            request = DeleteTrafficTemplateRequest.model_validate(payload)
        except ValidationError as exc:
            return failed("tg_delete_traffic_template", ErrorType.INVALID_PARAM, {"errors": exc.errors()})

        if self.store.template_in_use(request.template):
            return failed(
                "tg_delete_traffic_template",
                ErrorType.RESOURCE_CONFLICT,
                {"template": request.template},
            )

        path = self._template_path(request.template)
        if path is None:
            return failed(
                "tg_delete_traffic_template",
                ErrorType.RESOURCE_NOT_FOUND,
                {"template": request.template},
            )
        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            return failed("tg_delete_traffic_template", ErrorType.INTERNAL_ERROR, {"message": str(exc)})
        self.store.templates.pop(request.template, None)
        return success("tg_delete_traffic_template", {"template": request.template, "deleted": True})

    def _template_path(self, template: str) -> Path | None:
        if template in self.store.templates:
            return self.store.templates[template]
        path = self.settings.template_dir / f"{template}.yaml"
        if path.exists():
            self.store.templates[template] = path
            return path
        return None


def build_service_registry(service: TrexOperationService) -> dict[str, Any]:
    return {
        "tg_config_interface": service.config_interface,
        "tg_apply_traffic_template": service.apply_traffic_template,
        "tg_start_traffic_stream": service.start_traffic_stream,
        "tg_verify_traffic_loss": service.verify_traffic_loss,
        "tg_stop_traffic_stream": service.stop_traffic_stream,
        "tg_delete_traffic_template": service.delete_traffic_template,
    }


def _build_client(backend: str) -> TrexClient:
    if backend == "real":
        return TrexPythonApiClient()
    return SimulatedTrexClient()
