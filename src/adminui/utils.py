import datetime
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, TypeAlias

from offspot_config.utils.yaml import yaml_dump, yaml_load

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


def run_command(args: list[str]) -> CompletedProcess[str]:
    ps = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    return CompletedProcess(
        args=ps.args,
        returncode=ps.returncode,
        stdout=ps.stdout.strip() if ps.stdout else "",
    )
