import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.cases import router as cases_router
from app.config import settings, ConfigError
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings.validate()
    except ConfigError as e:
        print(f"\n[STARTUP ERROR] {e}\n", file=sys.stderr)
        sys.exit(1)
    await init_db()
    yield


app = FastAPI(
    title="PayState Bridge API",
    description="Resolves payment ambiguity before retrying. Synthetic data + Test Mode only.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.webhooks import router as webhooks_router
from app.sim.stream import router as sim_router
from app.api.recover import router as recover_router

app.include_router(health_router)
app.include_router(cases_router)
app.include_router(webhooks_router)
app.include_router(sim_router)
app.include_router(recover_router)


@app.get("/")
async def root() -> dict:
    return {
        "service": "PayState Bridge API",
        "version": "0.1.0",
        "environment": "demo",
        "disclaimer": "Synthetic data and Razorpay Test Mode only.",
    }
