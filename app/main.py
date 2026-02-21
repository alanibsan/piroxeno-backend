from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.core.logging_config import setup_logging
from app.core.request_middleware import logging_middleware
from app.routes.metrics import router as metrics_router



# 🔥 Inicializar logging ANTES de crear app
setup_logging()

app = FastAPI(
    title="AI Chat SaaS",
    version="1.0"
)

# Middleware de logging
app.middleware("http")(logging_middleware)

# CORS (luego lo restringimos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(metrics_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
