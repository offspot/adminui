from http import HTTPStatus

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from adminui.auth.session import Session
from adminui.auth.views import login_required
from adminui.constants import TEMPLATES_DIR
from adminui.context import Context
from adminui.hostbridge import bridge

context = Context.get()
router = APIRouter(prefix="", tags=["frontend"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", name="home")
def home(request: Request, session: Session = Depends(login_required)) -> Response:
    return templates.TemplateResponse(
        request=request, name="home.html", context={"session": session, "ctx": context}
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
