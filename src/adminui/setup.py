import re
from dataclasses import dataclass

from offspot_config.utils.yaml import yaml_load

from adminui.constants import DOCKER_COMPOSE_PATH, HOSTAPD_CONF_PATH, logger
from adminui.context import Context
from adminui.hostbridge import bridge
from adminui.utils import read_offspot_conf


class MissingType:
    """Custom type for information not found in source (different than None)"""


Missing = MissingType()  # single value used to check if its missing


@dataclass
class Capabilities:
    change_ssid: bool = False
    change_bootorder: bool = False


@dataclass
class ComposeData:
    """useful information read from compose.yaml"""

    tld: str
    domain: str
    admin_password: str

    kiwix_prefix: str = "browse"
    contentfilter_prefix: str = "filter"

    has_clock: bool = False
    has_filemanager: bool = False
    has_zimmanager: bool = False
    has_metrics: bool = False
    has_contentfilter: bool = False


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

    has_clock = has_filemanager = has_zimmanager = has_metrics = has_contentfilter = (
        False
    )
    kiwix_prefix = "kiwix"
    contentfilter_prefix = "filter"
    admin_password = ""
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
        if svc_id == "contentfilter":
            has_contentfilter = True
            contentfilter_prefix = svc_name.split(":", 1)[0]

    # first service defining ADMIN_PASSWORD is considered hoilding proper value
    for svc in compose["services"].values():
        passwd = svc.get("environment", {}).get("ADMIN_PASSWORD")
        if passwd is not None:
            admin_password = passwd
            break

    return ComposeData(
        tld=tld,
        domain=domain,
        admin_password=admin_password,
        kiwix_prefix=kiwix_prefix,
        contentfilter_prefix=contentfilter_prefix,
        has_clock=has_clock,
        has_zimmanager=has_zimmanager,
        has_filemanager=has_filemanager,
        has_metrics=has_metrics,
        has_contentfilter=has_contentfilter,
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
        capabilities.change_ssid = cap.get("change_ssid")
        capabilities.change_bootorder = cap.get("change_bootorder")
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
        if conf.ssid is Missing and (match := ssid_re.match(line)):
            conf.ssid = match.groupdict()["value"]

        if conf.passphrase is Missing and (match := passphrase_re.match(line)):
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


def get_wifi_conf() -> WifiConf:
    # read wifi conf from offspot.yaml if present
    wifi_conf = get_wifi_conf_from_offspot_yaml()
    if not wifi_conf.is_complete:
        # otherwise read from hostapd.conf
        wifi_conf = complete_wifi_conf_from_hostapd(wifi_conf)
    return wifi_conf


def prepare_context():
    # read tld, domain, prefixes from compose
    compose_data = get_from_compose()

    # read capabilities
    capabilities = get_capabilities_from_config()

    # read wifi conf
    # /!\ at this stage, hostapd.conf might not exists
    # and thus conf might be composed of ap: in offspot.yamll or defaults
    # /!\ it's possible ap: references perf profile but ap.py will switch to coverage
    wifi_conf = get_wifi_conf()

    # request sshd service status from bridge
    try:
        sshd_enabled = bridge.request_service_enabled("ssh").is_enabled
    except Exception:
        sshd_enabled = False

    # request boot-order from bridge
    try:
        bootorder = re.sub(r"^BOOT_ORDER=", "", bridge.request_bootorder().value)
    except Exception:
        bootorder = Context.bootorder

    Context.setup(
        tld=compose_data.tld,
        domain=compose_data.domain,
        admin_password=compose_data.admin_password,
        bootorder=bootorder,
        kiwix_prefix=compose_data.kiwix_prefix,
        contentfilter_prefix=compose_data.contentfilter_prefix,
        has_clock=compose_data.has_clock,
        has_zimmanager=compose_data.has_zimmanager,
        has_filemanager=compose_data.has_filemanager,
        has_metrics=compose_data.has_metrics,
        has_contentfilter=compose_data.has_contentfilter,
        can_change_ssid=capabilities.change_ssid,
        can_change_bootorder=capabilities.change_bootorder,
        wifi_profile=wifi_conf.profile,
        wifi_ssid=wifi_conf.ssid,
        wifi_passphrase=wifi_conf.passphrase,
        sshd_enabled=sshd_enabled,
    )
