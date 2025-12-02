import logging
import os
from pathlib import Path

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME") or "missing"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or "missing"

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME") or "session_id"
DEFAULT_SESSION_DURATION_MN = int(os.getenv("DEFAULT_SESSION_DURATION_MN") or "60")

TEMPLATES_DIR = Path(__file__).with_name("templates")
STATIC_DIR = (
    Path(os.getenv("STATIC_DIR", "/tmp"))
    if os.getenv("STATIC_DIR")
    else Path(__file__).with_name("static")
)

# integration
BRIDGE_SOCKET = Path(os.getenv("BRIDGE_SOCKET") or "/run/offspot/mekhenet.sock")
OFFSPOT_YAML_PATH = Path(
    os.getenv("OFFSPOT_YAML_PATH") or "/boot/firmware/offspot.yaml"
)
LATEST_YAML_PATH = Path(os.getenv("LATEST_YAML_PATH") or "/etc/offspot/latest.yaml")
DOCKER_COMPOSE_PATH = Path(
    os.getenv("DOCKER_COMPOSE_PATH") or "/etc/docker/compose.yml"
)
HOSTAPD_CONF_PATH = Path(os.getenv("HOSTAPD_CONF_PATH") or "/etc/hostapd/hostapd.conf")

logging.basicConfig(level=logging.DEBUG if bool(os.getenv("DEBUG")) else logging.INFO)
logger = logging.getLogger("adminui")
