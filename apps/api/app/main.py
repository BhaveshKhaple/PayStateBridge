from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router

app = FastAPI(
    title="PayState Bridge API",
    description="Resolves payment ambiguity before retrying. Synthetic data + Test Mode only.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


@app.get("/")
async def root() -> dict:
    return {
        "service": "PayState Bridge API",
        "version": "0.1.0",
        "environment": "demo",
        "disclaimer": "Synthetic data and Razorpay Test Mode only.",
    }
