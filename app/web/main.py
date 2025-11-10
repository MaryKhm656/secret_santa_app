from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.web import routes


def create_app() -> FastAPI:
    """
    Factory for creating a FastAPI Secret Santa application

    """
    app = FastAPI(title="SecretSanta", log_level="debug")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(routes.router)
    return app
