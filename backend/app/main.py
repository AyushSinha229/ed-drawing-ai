from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.config import settings
from app.core.storage import ensure_storage
from app.db import Base, engine
from app.routers import results, uploads


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ensure_storage()
    Base.metadata.create_all(bind=engine)
    app.include_router(uploads.router, prefix=settings.api_prefix)
    app.include_router(results.router, prefix=settings.api_prefix)
    app.mount("/static", StaticFiles(directory=str(settings.storage_dir)), name="static")
    return app


app = create_app()


@app.get("/")
async def root():
    return {"name": settings.app_name, "status": "ok"}
