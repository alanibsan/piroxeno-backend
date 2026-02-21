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
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Piroxeno AI API</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: radial-gradient(circle at center, #1e293b 0%, #0f172a 60%);
                color: #f8fafc;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                text-align: center;
            }
            .card {
                padding: 40px;
                border-radius: 16px;
                background: rgba(30, 41, 59, 0.6);
                backdrop-filter: blur(10px);
                box-shadow: 0 20px 60px rgba(0,0,0,0.6);
            }
            h1 {
                font-size: 32px;
                margin-bottom: 10px;
            }
            .status {
                margin: 15px 0;
                font-weight: 600;
                font-size: 16px;
            }
            .dot {
                height: 10px;
                width: 10px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 8px;
            }
            code {
                color: #38bdf8;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🧠 Piroxeno AI API</h1>
            <div class="status" id="status">
                <span class="dot" style="background:#facc15;"></span>
                Checking status...
            </div>
            <p>Endpoint: <code>POST /chat</code></p>
            <p>Health: <code>GET /health</code></p>
        </div>

        <script>
            fetch('/health')
                .then(res => res.json())
                .then(data => {
                    const statusEl = document.getElementById('status');
                    statusEl.innerHTML = `
                        <span class="dot" style="background:#22c55e;"></span>
                        Online
                    `;
                })
                .catch(() => {
                    const statusEl = document.getElementById('status');
                    statusEl.innerHTML = `
                        <span class="dot" style="background:#ef4444;"></span>
                        Offline
                    `;
                });
        </script>
    </body>
    </html>
    """