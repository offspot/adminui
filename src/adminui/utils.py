import datetime
from pathlib import Path
from typing import Any

from offspot_config.utils.yaml import yaml_dump, yaml_load
from typing_extensions import TypeAlias

from adminui.constants import LATEST_YAML_PATH, OFFSPOT_YAML_PATH

ValidateResult: TypeAlias = tuple[bool, dict[str, str]]


def get_now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


def read_yaml_config(path: Path) -> dict[str, Any]:
    return yaml_load(path.read_text()) or {}


def read_offspot_conf() -> dict[str, Any]:
    return read_yaml_config(OFFSPOT_YAML_PATH)


def read_latest_conf() -> dict[str, Any]:
    return read_yaml_config(LATEST_YAML_PATH)


def save_offspot_conf(conf: dict[str, Any]):
    OFFSPOT_YAML_PATH.write_text("---\n" if not conf else yaml_dump(conf))
