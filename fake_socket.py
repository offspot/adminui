import json
import os
from http import HTTPStatus

from fabric import Connection
from fastapi import FastAPI
from fastapi.responses import JSONResponse

connect_to = os.getenv("PI_CONN", "user@h1")
socket_on_host = os.getenv("SOCKET_ON_HOST", "/run/offspot/mekhenet.sock")

app = FastAPI()


@app.get("{path:path}")
def handle_request(path: str):
    print(f"QUERY: {path}")
    command = "curl -w '\nHTTP:%{http_code}\n'"
    curl = Connection(connect_to).run(
        f"{command} --unix-socket {socket_on_host} http://host{path}",
        hide=True,
    )
    if not curl.ok:
        return JSONResponse(
            {
                "succeeded": False,
                "details": f"fake curl command failed: {curl.stdout.strip()}",
            }
        )
    lines = curl.stdout.strip().splitlines()
    status_code = HTTPStatus(int(lines.pop().strip().split("HTTP:", 1)[-1]))
    print(f"HTTP: {status_code} {status_code._name_}")
    payload = json.loads("\n".join(lines))
    print(f"> {payload}")
    return JSONResponse(content=payload, status_code=status_code)
