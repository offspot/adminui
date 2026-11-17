import re
from enum import StrEnum
from typing import Annotated, Self

import attrs
from attrs import define, field
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.templating import Jinja2Templates
from pydantic.main import BaseModel

from adminui.auth.session import Session
from adminui.auth.views import login_required
from adminui.constants import TEMPLATES_DIR, logger
from adminui.context import Context
from adminui.hostbridge import bridge
from adminui.utils import (
    ValidateResult,
)

router = APIRouter(prefix="/bootorder", tags=["system"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)
context = Context.get()


class BootValue(StrEnum):
    SD_CARD_DETECT = "0"
    SD_CARD = "1"
    NETWORK = "2"
    RPIBOOT = "3"
    USB_MSD = "4"
    BCM_USB_MSD = "5"
    NVME = "6"
    HTTP = "7"
    STOP = "e"
    RESTART = "f"


@define
class BootOrder:
    value: str = field(
        validator=attrs.validators.matches_re(r"^0X[0-9A-Fa-f]+$", re.IGNORECASE)
    )

    @property
    def entries(self) -> list[BootValue]:
        return [BootValue(entry) for entry in reversed(self.value[2:])]

    @property
    def first(self) -> BootValue:
        return self.entries[0]

    def __str__(self) -> str:
        return ", ".join([bv.name for bv in self.entries])

    @classmethod
    def using(cls, args: list[BootValue]) -> "BootOrder":  # noqa: UP037
        return cls("0x" + "".join(reversed([bv.value for bv in args])))

    @classmethod
    def via(cls, *args: str) -> "BootOrder":  # noqa: UP037
        return cls(
            "0x" + "".join(reversed([getattr(BootValue, bv).value for bv in args]))
        )


class BootOrderData(BaseModel):
    value: str
    model_config = {"extra": "forbid"}

    @classmethod
    def options(cls, current: str) -> dict[str, str]:
        ours = {
            BootOrder.via(
                "SD_CARD", "NVME", "USB_MSD", "RESTART"
            ).value: "Boot from SD",
            BootOrder.via("USB_MSD", "SD_CARD", "RESTART").value: "Boot from USB",
            BootOrder.via(
                "NVME", "USB_MSD", "SD_CARD", "HTTP", "RESTART"
            ).value: "Kiwix H1 (NVME, USB, SD)",
            BootOrder.via(
                "USB_MSD", "NVME", "SD_CARD", "HTTP", "RESTART"
            ).value: "Kiwix H1, boot from USB",
        }

        if current not in ours:
            try:
                bo = BootOrder(value=current)
                ours[bo.value] = f"{bo!s} (yours)"
            except Exception:
                ours[current] = f"{current!s} (yours)"

        return ours

    @classmethod
    def ctx_defaults(cls) -> Self:
        return cls(
            value=context.bootorder,
        )

    def validate(self) -> ValidateResult:
        errors = {}
        try:
            BootOrder(value=self.value)
        except Exception:
            errors["value"] = "Invalid BootOrder value"
        return not errors, errors


@router.get("/", name="bootorder_config")
def config(request: Request, session: Session = Depends(login_required)) -> Response:
    print(f"----------------{context.bootorder}-------")
    return templates.TemplateResponse(
        request=request,
        name="bootorder/config.html",
        context={
            "ctx": context,
            "errors": {},
            "form": BootOrderData.ctx_defaults(),
        },
    )


@router.post("/")
def config_update(
    request: Request,
    data: Annotated[BootOrderData, Form()],
    session: Session = Depends(login_required),
) -> Response:
    is_valid, errors = data.validate()
    if is_valid:
        try:
            update_bootorder = bridge.request_bootorder_update(bootorder=data.value)
            if not update_bootorder.succeeded:
                raise (
                    update_bootorder.call_exception
                    if update_bootorder.call_exception
                    else OSError(str(update_bootorder))
                )
            # update context
            context.bootorder = data.value
        except Exception as exc:
            logger.error(f"failed to update bootorder: {exc}")
            logger.exception(exc)
            errors["all"] = f"Failed to record changes: [{type(exc).__name__}] {exc!s}"
        else:
            return templates.TemplateResponse(
                request=request, name="reboot_required.html", context={"ctx": context}
            )
    return templates.TemplateResponse(
        request=request,
        name="bootorder/config.html",
        context={"ctx": context, "errors": errors, "form": data},
    )
