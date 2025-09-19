from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings

# Agar tumhare existing routers hain, import karo yahan
# Example:
# from app.api.upload import router as upload_router
# from app.api.summarize import router as summarize_router
# from app.api.chat import router as chat_router
# from app.api.search import router as search_router

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        description="API for Legal Contract Processing: Upload, Summarize, Chat, and Search",
        version="1.0.0",
    )

    # -------------------------
    # CORS Middleware
    # -------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Dev; restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------
    # Root Route (for Vercel check)
    # -------------------------
    @app.get("/", tags=["Root"])
    def root():
        return {"message": "Backend is running on Vercel!"}

    # -------------------------
    # Existing API Routers
    # -------------------------
    # Example:
    # app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
    # app.include_router(summarize_router, prefix="/api/summarize", tags=["Summarize"])
    # app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    # app.include_router(search_router, prefix="/api/search", tags=["Search"])

    # -------------------------
    # Health Check
    # -------------------------
    @app.get("/api/health", tags=["Health"])
    def health():
        return {"status": "ok", "app": settings.app_name}

    # -------------------------
    # Serve Frontend
    # -------------------------
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")

    if os.path.exists(frontend_dir):
        # Serve static files like JS, CSS
        app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

        # Serve index.html for all other routes
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            index_file = os.path.join(frontend_dir, "index.html")
            return FileResponse(index_file)

    return app


# -------------------------
# Create app instance
# -------------------------
app = create_app()
