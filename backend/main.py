"""FastAPI entrypoint for the rPPG stress dashboard."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes_dataset, routes_demo, routes_evaluation, routes_features, routes_training


def create_app() -> FastAPI:
    app = FastAPI(
        title="rPPG Stress API",
        description="Backend bridge for the academic rPPG stress estimation pipeline.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_dataset.router, prefix="/api")
    app.include_router(routes_features.router, prefix="/api")
    app.include_router(routes_training.router, prefix="/api")
    app.include_router(routes_evaluation.router, prefix="/api")
    app.include_router(routes_demo.router, prefix="/api")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rppg-stress-api"}

    return app


app = create_app()
