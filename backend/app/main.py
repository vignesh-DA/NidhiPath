"""
NidhiPath — FastAPI Application Entrypoint

AI-Driven Scheme Matching for Marginalized Entrepreneurs (NSFDC, MoSJE)

Core principle: Steps 1-5 of the user journey work with ZERO AI-model
dependency. If the LLM intake or RAG Q&A layer goes down, the form-path
recommendation, calculator, and locator still work end-to-end.
AI enhances the experience; it never gates the critical path.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes_recommender import router as recommender_router
from app.api.routes_calculator import router as calculator_router
from app.api.routes_locator import router as locator_router
from app.api.routes_rag import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown logic."""
    # Startup
    print("=" * 60)
    print("  NidhiPath API — Starting up")
    print(f"  Environment: {settings.APP_ENV}")
    print(f"  Supabase: {'configured' if settings.has_supabase else 'NOT configured (using JSON files)'}")
    print(f"  Groq: {'configured' if settings.has_groq else 'NOT configured (Module 4 will be stubbed)'}")
    print(f"  Data dir: {settings.DATA_DIR}")
    print("=" * 60)
    yield
    # Shutdown
    print("NidhiPath API — Shutting down")


app = FastAPI(
    title="NidhiPath API",
    description=(
        "AI-Driven Scheme Matching for Marginalized Entrepreneurs. "
        "Helps SC beneficiaries find concessional credit schemes (NSFDC), "
        "calculate EMIs, and locate authorized channel partners."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(recommender_router, prefix="/api/v1", tags=["Scheme Recommender"])
app.include_router(calculator_router, prefix="/api/v1", tags=["Financial Calculator"])
app.include_router(locator_router, prefix="/api/v1", tags=["Partner Locator"])
app.include_router(rag_router, prefix="/api/v1", tags=["LLM Intake + RAG Q&A"])


@app.get("/", tags=["Health"])
async def root():
    """Health check / API info."""
    return {
        "name": "NidhiPath API",
        "version": "0.1.0",
        "status": "healthy",
         "modules": {
             "recommender": "active",
             "calculator": "active",
             "locator": "active",
             "rag": "active",
         },
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "supabase": "connected" if settings.has_supabase else "not_configured",
        "groq": "connected" if settings.has_groq else "not_configured",
        "data_dir": str(settings.DATA_DIR),
        "data_dir_exists": settings.DATA_DIR.exists(),
    }
