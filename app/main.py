from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

app = FastAPI(title="CRM Backend", version="0.0.1")

# Логи в stdout (видно на хостинге)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# CORS (пока открыто, сузим позже)
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
