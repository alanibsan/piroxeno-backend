from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.core.logging_config import setup_logging
from app.core.request_middleware import logging_middleware
from app.routes.metrics import router as metrics_router
from fastapi.responses import HTMLResponse


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



@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Piroxeno AI API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #0f172a;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .card {
                    text-align: center;
                }
                h1 {
                    margin-bottom: 10px;
                }
                .status {
                    color: #22c55e;
                    font-weight: bold;
                }
                .endpoint {
                    margin-top: 20px;
                    color: #94a3b8;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🧠 Piroxeno AI API</h1>
                <div class="status">● Online</div>
                <div class="endpoint">
                    Endpoint: POST /chat<br>
                    Health: GET /health
                </div>
            </div>
        </body>
    </html>
    """