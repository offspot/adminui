from dataclasses import dataclass
from http import HTTPStatus

import httpx

from adminui.constants import BRIDGE_SOCKET


@dataclass
class BridgeResponse:
    succeeded: bool
    enabled: bool | None = None
    call_exception: Exception | None = None
    http_code: HTTPStatus = HTTPStatus.IM_A_TEAPOT
    details: str = ""

    @property
    def is_enabled(self) -> bool:
        if self.enabled is None:
            raise OSError("enabled not set")
        return self.enabled

    @property
    def http_error(self) -> bool:
        return self.http_code != HTTPStatus.OK

    def __str__(self) -> str:
        if self.succeeded:
            if self.enabled is not None:
                return f"OK enabled={self.enabled}"
            return "OK"
        if self.call_exception:
            return str(self.call_exception)
        if not self.http_error and self.details:
            return self.details
        return (
            f"HTTP {self.http_code!s} {self.http_code._name_}"
            f"{' ' if self.details else ''}{self.details}"
        )


class Bridge:
    def __init__(self):
        # doesn't matter in this context
        self.api_url = "http://host"
        # custom transport over UDS
        self.transport = httpx.HTTPTransport(uds=str(BRIDGE_SOCKET))

    def do_request(self, path: str) -> BridgeResponse:
        try:
            with httpx.Client(transport=self.transport) as client:
                response = client.get(f"{self.api_url}{path}")

                if response.status_code != 200:
                    return BridgeResponse(
                        succeeded=False,
                        http_code=HTTPStatus(response.status_code),
                    )
                try:
                    succeeded = response.json().get("success") or False
                    details = response.json().get("details") or ""
                    enabled = response.json().get("enabled")
                except Exception:
                    return BridgeResponse(
                        succeeded=False,
                        http_code=HTTPStatus(response.status_code),
                        details="Failed to parse: {exc!s}",
                    )
                return BridgeResponse(
                    succeeded=succeeded,
                    http_code=HTTPStatus(response.status_code),
                    details=details,
                    enabled=enabled,
                )
        except Exception as exc:
            return BridgeResponse(succeeded=False, call_exception=exc)

    def request_restart(self, after_seconds: int) -> BridgeResponse:
        """restart Host device after a defined number of seconds"""
        return self.do_request(path=f"/reboot/{after_seconds}")

    def request_service_toggle(self, name: str, enable: bool) -> BridgeResponse:
        """enable (not start) systemd service"""
        action = "enable" if enable else "disable"
        return self.do_request(path=f"/toggle-service/{action}/{name}")

    def request_service_enabled(self, name: str) -> BridgeResponse:
        return self.do_request(path=f"/service-is-enabled/{name}")


bridge = Bridge()
