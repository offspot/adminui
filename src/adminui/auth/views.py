from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Cookie, Response
from fastapi.params import Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from adminui.auth import RequiresLoginException, are_valid_credentials
from adminui.auth.session import Session, session_manager
from adminui.constants import SESSION_COOKIE_NAME, TEMPLATES_DIR, logger
from adminui.context import Context

context = Context.get()
templates = Jinja2Templates(directory=TEMPLATES_DIR)
router = APIRouter(prefix="/auth", tags=["auth"])


def requires_login_exception_handler(request: Request, exc: Exception) -> Response:
    return RedirectResponse(
        url=router.url_path_for("login"), status_code=HTTPStatus.FOUND
    )


def login_required(session_id: str | None = Cookie(default=None)) -> Session:
    if session_id is None:
        logger.debug(f"No `{SESSION_COOKIE_NAME}` cookie")
        raise RequiresLoginException
    session = session_manager.get(session_id)
    if not session:
        logger.debug(f"Session {session_id} not in manager")
        raise RequiresLoginException
    if not session.is_valid:
        logger.debug(f"Session {session_id} not valid anymore")
        raise RequiresLoginException
    return session


@router.get("/login", name="login")
def login(
    request: Request, is_incorrect: bool = False, message_content: str = ""
) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "ctx": context,
            "is_incorrect": is_incorrect,
            "message_content": message_content,
        },
    )


@router.post("/login", name="login_auth")
def login_auth(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    return_to: Annotated[str, Form()] | str = "/",
) -> Response:
    if are_valid_credentials(username=username, password=password):
        session = session_manager.create()
        response = RedirectResponse(url=return_to, status_code=HTTPStatus.FOUND)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=str(session.id),
            expires=session.expire_on,
            httponly=True,
        )
        return response
    return login(request, is_incorrect=True, message_content="Invalid credentials.")


@router.get("/logout", name="logout")
def logout(request: Request, session_id: str | None = Cookie(default=None)):
    if session_id:
        session_manager.remove(session_id)
    response = RedirectResponse(url=context.hotspot_url, status_code=HTTPStatus.FOUND)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response
