from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.templating import Jinja2Templates
from pydantic.main import BaseModel

from adminui.auth.session import Session
from adminui.auth.views import login_required
from adminui.constants import TEMPLATES_DIR, logger
from adminui.context import Context
from adminui.hostbridge import bridge
from adminui.utils import ValidateResult

router = APIRouter(prefix="/optional", tags=["optional", "ssh", "screen"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)
context = Context.get()


def request_ssh_config(enable: bool) -> bool:
    logger.info(f"{'dis' if enable else 'en'}abled SSHd")
    toggle = bridge.request_service_toggle(name="ssh", enable=enable)
    return toggle.succeeded


class OptionalFormData(BaseModel):
    sshd: bool = False  # req. HTML forms dont send off checkboxes
    kiosk: bool = False  # req. HTML forms dont send off checkboxes
    model_config = {"extra": "forbid"}

    @classmethod
    def ctx_defaults(cls) -> OptionalFormData:
        return OptionalFormData(sshd=context.sshd_enabled, kiosk=context.kiosk_enabled)

    def validate(self) -> ValidateResult:
        errors: dict[str, str] = {}
        if not isinstance(self.sshd, bool):
            errors["sshd"] = "Must be enabled or disabled."
        if self.kiosk is not False:
            errors["kiosk"] = "Kiosk is not available at the moment."
        return not errors, errors


@router.get("/", name="optional_config")
def config(request: Request, session: Session = Depends(login_required)) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="optional/config.html",
        context={"ctx": context, "errors": {}, "form": OptionalFormData.ctx_defaults()},
    )


@router.post("/")
def config_update(
    request: Request,
    data: Annotated[OptionalFormData, Form()],
    session: Session = Depends(login_required),
) -> Response:
    is_valid, errors = data.validate()
    if is_valid:
        try:
            toggle_ssh = bridge.request_service_toggle(name="ssh", enable=data.sshd)
            if not toggle_ssh.succeeded:
                raise (
                    toggle_ssh.call_exception
                    if toggle_ssh.call_exception
                    else OSError(str(toggle_ssh))
                )
            # update context
            context.sshd_enabled = data.sshd
        except Exception as exc:
            logger.error(f"failed to record Optional features: {exc}")
            logger.exception(exc)
            errors["all"] = f"Failed to record changes: [{type(exc).__name__}] {exc!s}"
        else:
            return templates.TemplateResponse(
                request=request, name="reboot_required.html", context={"ctx": context}
            )
    return templates.TemplateResponse(
        request=request,
        name="optional/config.html",
        context={"ctx": context, "errors": errors, "form": data},
    )
