import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from adminui.constants import STATIC_DIR
from adminui.setup import prepare_context

prepare_context()


def create_app(*, debug: bool = True):
    from adminui import frontend
    from adminui.__about__ import __description__, __version__
    from adminui.auth import RequiresLoginException
    from adminui.auth.views import requires_login_exception_handler
    from adminui.auth.views import router as auth_router
    from adminui.optional import router as optional_router
    from adminui.wifi import router as wifi_router

    app = FastAPI(
        debug=debug,
        docs_url="/docs",
        title="Admin UI",
        version=__version__,
        description=__description__,
    )

    app.add_exception_handler(RequiresLoginException, requires_login_exception_handler)

    if origins := os.getenv("ALLOWED_ORIGINS", None):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins.split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(auth_router)
    app.include_router(router=frontend.router)
    app.include_router(router=wifi_router)
    app.include_router(router=optional_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    return app


app = create_app()
