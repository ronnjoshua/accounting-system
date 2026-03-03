from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Build CORS origins list
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add FRONTEND_URL if set
if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_origins:
    cors_origins.append(settings.FRONTEND_URL)

# Add additional origins from CORS_ORIGINS env var (comma-separated)
if settings.CORS_ORIGINS:
    additional_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    cors_origins.extend(additional_origins)

# Remove duplicates while preserving order
cors_origins = list(dict.fromkeys(cors_origins))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
