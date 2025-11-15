from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.templating import Jinja2Templates
from offspot_runtime.checks import (
    is_valid_profile,
    is_valid_ssid,
    is_valid_wpa2_passphrase,
)
from pydantic.main import BaseModel

from adminui.auth.session import Session
from adminui.auth.views import login_required
from adminui.constants import TEMPLATES_DIR, logger
from adminui.context import Context
from adminui.utils import (
    ValidateResult,
    read_latest_conf,
    read_offspot_conf,
    save_offspot_conf,
)

router = APIRouter(prefix="/wifi", tags=["wifi"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)
context = Context.get()


class WifiFormData(BaseModel):
    profile: str
    ssid: str
    open: bool = False  # req. HTML forms dont send off checkboxes
    passphrase: str
    model_config = {"extra": "forbid"}

    @classmethod
    def ctx_defaults(cls) -> WifiFormData:
        return WifiFormData(
            profile=context.wifi_profile,
            ssid=context.wifi_ssid,
            open=context.wifi_open,
            passphrase=context.wifi_passphrase or "",
        )

    def validate(self) -> ValidateResult:
        errors = {}
        valid = is_valid_profile(self.profile)
        if not valid:
            errors["profile"] = valid.help_text
        valid = is_valid_ssid(self.ssid)
        if not valid:
            errors["ssid"] = valid.help_text
        if not self.open:
            valid = is_valid_wpa2_passphrase(self.passphrase)
            if not valid:
                errors["passphrase"] = valid.help_text
        else:
            self.passphrase = context.wifi_passphrase or ""
        return not errors, errors


def update_wifi_config(data: WifiFormData):
    latest = read_latest_conf()
    config = read_offspot_conf()
    ap = config.get("ap", latest.get("ap", {}))
    ap["ssid"] = data.ssid
    ap["profile"] = data.profile
    ap["passphrase"] = None if data.open else data.passphrase
    config["ap"] = ap
    save_offspot_conf(config)


@router.get("/", name="wifi_config")
def config(request: Request, session: Session = Depends(login_required)) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="wifi/config.html",
        context={"ctx": context, "errors": {}, "form": WifiFormData.ctx_defaults()},
    )


@router.post("/")
def config_update(
    request: Request,
    data: Annotated[WifiFormData, Form()],
    session: Session = Depends(login_required),
) -> Response:
    is_valid, errors = data.validate()
    if is_valid:
        try:
            update_wifi_config(data=data)
            # update context
            context.wifi_profile = data.profile
            context.wifi_ssid = data.ssid
            context.wifi_passphrase = None if data.open else data.passphrase
        except Exception as exc:
            logger.error(f"failed to record WiFi conf: {exc}")
            logger.exception(exc)
            errors["all"] = f"Failed to record changes: [{type(exc).__name__}] {exc!s}"
        else:
            return templates.TemplateResponse(
                request=request, name="reboot_required.html", context={"ctx": context}
            )
    return templates.TemplateResponse(
        request=request,
        name="wifi/config.html",
        context={"ctx": context, "errors": errors, "form": data},
    )
