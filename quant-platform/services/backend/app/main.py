from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .api.routes import register_routes


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        docs_url=settings.api_docs_url,
        openapi_url=settings.api_openapi_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*" if settings.frontend_base_url is None else str(settings.frontend_base_url)],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routes(app)

    return app


app = create_app()
