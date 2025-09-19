from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.health import router as health_router
    app.include_router(health_router, prefix="/api")

    from app.api.upload import router as upload_router
    from app.api.summarize import router as summarize_router
    from app.api.chat import router as chat_router
    from app.api.search import router as search_router

    app.include_router(upload_router, prefix="/api")
    app.include_router(summarize_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(search_router, prefix="/api")

    return app


app = create_app()


 
 