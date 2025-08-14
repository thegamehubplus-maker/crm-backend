from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.routers import auth as auth_router
from app.routers import contacts as contacts_router
from app.idempotency import IdempotencyMiddleware


app = FastAPI(title="CRM Backend", version="0.0.1")

# Configure logging to stdout using LOG_LEVEL from environment
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# CORS configuration: allow origins from env variable (comma-separated) or '*'
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add idempotency middleware for POST/PUT/PATCH requests
app.add_middleware(IdempotencyMiddleware)

# Include routers for auth and contacts
app.include_router(auth_router.router)
app.include_router(contacts_router.router)


@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"status": "ok"}