from http import HTTPStatus

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic.main import BaseModel

from adminui.auth.session import Session
from adminui.auth.views import login_required
from adminui.constants import TEMPLATES_DIR
from adminui.context import Context
from adminui.hostbridge import bridge

context = Context.get()
router = APIRouter(prefix="", tags=["frontend"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class Link(BaseModel):
    url: str
    title: str
    text: str


@router.get("/", name="home")
def home(request: Request, session: Session = Depends(login_required)) -> Response:
    links: list[Link] = []
    if context.has_clock:
        links.append(
            Link(
                url=f"http://clock.{context.fqdn}/",
                title="Clock",
                text="Update date and time as seen by the Hotspot.",
            )
        )
    if context.has_zimmanager:
        links.append(
            Link(
                url=f"http://zim-manager.{context.fqdn}/",
                title="ZIM Manager",
                text="Add or remove content (ZIM files).",
            )
        )
    if context.has_filemanager:
        links.append(
            Link(
                url=f"http://resources.{context.fqdn}/admin/?p=",
                title="File Manager",
                text="Add, move, delete files visible in File Manager app.",
            )
        )
    if context.has_metrics:
        links.append(
            Link(
                url=f"http://metrics.{context.fqdn}/",
                title="Metrics",
                text="See your Hotspot's usage statistics.",
            )
        )
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"session": session, "ctx": context, "links": links},
    )


@router.get("/restart")
def redirect_to_home(
    request: Request, session: Session = Depends(login_required)
) -> Response:
    return RedirectResponse(
        url=router.url_path_for("home"), status_code=HTTPStatus.FOUND
    )


@router.post("/restart", name="restart")
def restart(request: Request, session: Session = Depends(login_required)) -> Response:
    restarted = bridge.request_restart(context.reboot_after_seconds)
    return templates.TemplateResponse(
        request=request,
        name="rebooting.html",
        context={"session": session, "rebooting": restarted.succeeded, "ctx": context},
    )
