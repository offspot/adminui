import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(kw_only=True)
class Context:
    # singleton instance
    _instance: "Context | None" = None
    devel: bool = False

    reboot_after_seconds: int = 5

    tld: str = "hotspot"
    domain: str = "kiwix"

    kiwix_prefix: str = "browse"
    # zimdl_prefix: str = "zim-download"
    # contentfilter_prefix: str = "contentfilter"
    # filemanager_prefix: str = "resources"

    # capabilities are restrictions on an hotspot
    # regarding edit features of the adminUI
    can_change_ssid: bool = False

    wifi_ssid: str = "Kiwix Hotspot"
    wifi_passphrase: str | None = None
    wifi_profile: str = "perf"

    sshd_enabled: bool = False
    kiosk_enabled: bool = False

    # links to other services
    has_clock: bool = False
    has_filemanager: bool = False
    has_zimmanager: bool = False
    has_metrics: bool = False

    @property
    def fqdn(self) -> str:
        return f"{self.domain}.{self.tld}"

    @property
    def hotspot_url(self) -> str:
        return f"http://{self.fqdn}/"

    @property
    def wifi_open(self) -> bool:
        return self.wifi_passphrase is None

    @property
    def systemctl_path(self) -> Path:
        return Path("/bin/echo") if self.devel else Path("/usr/bin/systemctl")

    def __post_init__(self):
        self.devel = bool(os.getenv("DEVEL", ""))

    @classmethod
    def setup(cls, **kwargs: Any):
        if cls._instance:
            raise OSError("Already inited Context")
        cls._instance = cls(**kwargs)
        cls._instance.__post_init__()

    @classmethod
    def get(cls) -> "Context":
        if not cls._instance:
            raise OSError("Uninitialized context")  # pragma: no cover
        return cls._instance
