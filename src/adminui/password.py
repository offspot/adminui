import string
from typing import Annotated, Self

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.templating import Jinja2Templates
from offspot_runtime.checks import CheckResponse
from pydantic.main import BaseModel

from adminui.auth.session import Session
from adminui.auth.views import login_required
from adminui.constants import TEMPLATES_DIR, logger
from adminui.context import Context
from adminui.hostbridge import bridge
from adminui.utils import (
    ValidateResult,
)

router = APIRouter(prefix="/password", tags=["system"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)
context = Context.get()


def is_valid_admin_pwd(admin_pwd: str) -> CheckResponse:
    # should move to offspot-config

    if len(admin_pwd) <= 31 and set(admin_pwd) <= set(
        string.ascii_uppercase + string.ascii_lowercase + string.digits + "-" + "_"
    ):
        return CheckResponse(True)
    return CheckResponse(
        False, "Invalid password: max 31 chars. letters, numbers, _ and -"
    )


class PasswordFormData(BaseModel):
    value: str
    model_config = {"extra": "forbid"}

    @classmethod
    def ctx_defaults(cls) -> Self:
        return cls(
            value=context.admin_password,
        )

    def validate(self) -> ValidateResult:
        errors = {}
        valid = is_valid_admin_pwd(self.value)
        if not valid:
            errors["value"] = valid.help_text
        return not errors, errors


@router.get("/", name="password_config")
def config(request: Request, session: Session = Depends(login_required)) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="password/config.html",
        context={"ctx": context, "errors": {}, "form": PasswordFormData.ctx_defaults()},
    )


@router.post("/")
def config_update(
    request: Request,
    data: Annotated[PasswordFormData, Form()],
    session: Session = Depends(login_required),
) -> Response:
    is_valid, errors = data.validate()
    if is_valid:
        try:
            update_pass = bridge.request_adminpass_update(adminpass=data.value)
            if not update_pass.succeeded:
                raise (
                    update_pass.call_exception
                    if update_pass.call_exception
                    else OSError(str(update_pass))
                )
            # update context
            context.admin_password = data.value
        except Exception as exc:
            logger.error(f"failed to update password: {exc}")
            logger.exception(exc)
            errors["all"] = f"Failed to record changes: [{type(exc).__name__}] {exc!s}"
        else:
            return templates.TemplateResponse(
                request=request, name="reboot_required.html", context={"ctx": context}
            )
    return templates.TemplateResponse(
        request=request,
        name="password/config.html",
        context={"ctx": context, "errors": errors, "form": data},
    )
