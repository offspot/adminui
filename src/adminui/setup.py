import re
from dataclasses import dataclass

from offspot_config.utils.yaml import yaml_load

from adminui.constants import DOCKER_COMPOSE_PATH, HOSTAPD_CONF_PATH, logger
from adminui.context import Context
from adminui.hostbridge import bridge
from adminui.utils import read_offspot_conf


class MissingType:
    """Custom type for information not found in source (different than None)"""

    ...


Missing = MissingType()  # single value used to check if its missing


@dataclass
class Capabilities:
    change_ssid: bool = False


@dataclass
class ComposeData:
    """useful information read from compose.yaml"""

    tld: str
    domain: str

    kiwix_prefix: str = "browse"

    has_clock: bool = False
    has_filemanager: bool = False
    has_zimmanager: bool = False
    has_metrics: bool = False


@dataclass
class WifiConf:
    """WiFi config read from different sources (offspot.yaml, hostapd.conf)"""

    profile: str | MissingType = Missing
    ssid: str | MissingType = Missing
    passphrase: str | None | MissingType = Missing

    @property
    def is_complete(self) -> bool:
        """whether all values have been retrieved"""
        return all(value is not Missing for value in self.__dict__.values())


def get_from_compose() -> ComposeData:
    """read compose.yaml and return expected data"""
    compose = yaml_load(DOCKER_COMPOSE_PATH.read_text())

    fqdn = compose["services"]["reverse-proxy"]["environment"]["FQDN"]
    domain, tld = fqdn.rsplit(".", 1)

    svc_names = compose["services"]["reverse-proxy"]["environment"]["SERVICES"].split(
        ","
    )

    has_clock = has_filemanager = has_zimmanager = has_metrics = False
    kiwix_prefix = "kiwix"
    for svc_name in svc_names:
        svc_id = svc_name.rsplit(":", 1)[-1]
        if svc_id == "kiwix":
            kiwix_prefix = svc_name.split(":", 1)[0]

        if svc_id == "hwclock":
            has_clock = True
        if svc_id == "zim-manager":
            has_zimmanager = True
        if svc_id == "resources":
            has_filemanager = True
        if svc_id == "metrics":
            has_metrics = True

    return ComposeData(
        tld=tld,
        domain=domain,
        kiwix_prefix=kiwix_prefix,
        has_clock=has_clock,
        has_zimmanager=has_zimmanager,
        has_filemanager=has_filemanager,
        has_metrics=has_metrics,
    )


def get_capabilities_from_config() -> Capabilities:
    capabilities = Capabilities()
    try:
        yaml_config = read_offspot_conf()
    except Exception as exc:
        logger.error(f"Failed to read capabilities from config: {exc}")
        logger.exception(exc)
    else:
        cap = yaml_config.get("capabilities", {})
        # only SSID change ATM
        capabilities.change_ssid = cap.get("change_ssid")
    return capabilities


def get_wifi_conf_from_offspot_yaml() -> WifiConf:
    """read offspot.yaml for updated-not-applied changes to WiFi conf"""
    conf = WifiConf()
    try:
        yaml_config = read_offspot_conf()
    except Exception as exc:
        logger.error(f"Failed to read offspot config: {exc}")
        logger.exception(exc)
    else:
        ap = yaml_config.get("ap", {})
        conf.profile = ap.get("profile", conf.profile)
        conf.ssid = ap.get("ssid", conf.ssid)
        conf.passphrase = ap.get("passphrase", conf.passphrase)
    return conf


def complete_wifi_conf_from_hostapd(conf: WifiConf) -> WifiConf:
    """read hostapd.conf for actual WiFi params"""
    ssid_re = re.compile(r"^ssid=(?P<value>.+)$")
    passphrase_re = re.compile(r"^wpa_passphrase=(?P<value>.+)$")
    lines = HOSTAPD_CONF_PATH.read_text().splitlines()
    for line in lines:
        if conf.ssid is Missing:
            if match := ssid_re.match(line):
                conf.ssid = match.groupdict()["value"]

        if conf.passphrase is Missing:
            if match := passphrase_re.match(line):
                conf.passphrase = match.groupdict()["value"]

        if conf.profile is Missing and line.strip() == "hw_mode=g":
            conf.profile = "coverage"

        if conf.profile is Missing and line.strip() == "ieee80211ac=1":
            conf.profile = "perf"

    if conf.passphrase is Missing:
        conf.passphrase = None

    if conf.profile is Missing:
        conf.profile = "coverage"

    return conf


def prepare_context():
    # read tld, domain, prefixes from compose
    compose_data = get_from_compose()

    # read capabilities
    capabilities = get_capabilities_from_config()

    # read wifi conf from offspot.yaml if present
    wifi_conf = get_wifi_conf_from_offspot_yaml()
    if not wifi_conf.is_complete:
        # otherwise read from hostapd.conf
        wifi_conf = complete_wifi_conf_from_hostapd(wifi_conf)

    # request sshd service status from bridge
    try:
        sshd_enabled = bridge.request_service_enabled("ssh").is_enabled
    except Exception:
        sshd_enabled = False

    Context.setup(
        tld=compose_data.tld,
        domain=compose_data.domain,
        kiwix_prefix=compose_data.kiwix_prefix,
        has_clock=compose_data.has_clock,
        has_zimmanager=compose_data.has_zimmanager,
        has_filemanager=compose_data.has_filemanager,
        has_metrics=compose_data.has_metrics,
        can_change_ssid=capabilities.change_ssid,
        wifi_profile=wifi_conf.profile,
        wifi_ssid=wifi_conf.ssid,
        wifi_passphrase=wifi_conf.passphrase,
        sshd_enabled=sshd_enabled,
    )
