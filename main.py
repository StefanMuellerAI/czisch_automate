from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, setup_logging
from app.routers import health, transform, extract, transfer, manage
from app.services.playwright_service import playwright_service

# Setup logging
logger = setup_logging()

# Initialize FastAPI app with OpenAPI metadata
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Include routers
app.include_router(health.router)
app.include_router(transform.router)
app.include_router(extract.router)
app.include_router(transfer.router)
app.include_router(manage.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await playwright_service.start()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    try:
        await playwright_service.stop()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
