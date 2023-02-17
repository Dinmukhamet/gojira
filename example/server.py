from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from my_auth.routes import routes
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection

from example.config import get_database, get_settings
from gojira.auth.middleware import BaseAuthentication


def on_error(conn: HTTPConnection, exc: Exception) -> Response:
    return JSONResponse(
        content={
            "detail": str(exc),
            "message": "Failed to authenticate user with given credentials.",
        },
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


app = FastAPI()
app.state.database = get_database()
app.add_middleware(
    AuthenticationMiddleware,
    backend=BaseAuthentication(settings=get_settings()),
    on_error=on_error,
)

app.include_router(routes.router)


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


@app.get("/ping")
async def pong(request: Request):
    if request.user.is_authenticated:
        return "pong"
