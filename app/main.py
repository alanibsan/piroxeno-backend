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
        <script src="/widget.js" defer></script>
    </body>
    </html>
    """
from fastapi.responses import Response

@app.get("/widget.js")
def widget():
    js_code = """
(function() {
    if (window.PiroxenoWidget) return;

    const container = document.createElement("div");
    container.style.position = "fixed";
    container.style.bottom = "20px";
    container.style.right = "20px";
    container.style.width = "350px";
    container.style.height = "500px";
    container.style.background = "#1e293b";
    container.style.borderRadius = "16px";
    container.style.boxShadow = "0 20px 60px rgba(0,0,0,0.5)";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.overflow = "hidden";
    container.style.zIndex = "9999";

    container.innerHTML = `
        <div style="padding:15px;background:#0f172a;color:white;font-weight:600;">
            🧠 Piroxeno AI
        </div>
        <div id="messages" style="flex:1;padding:10px;overflow:auto;color:white;font-size:14px;"></div>
        <div style="display:flex;border-top:1px solid #334155;">
            <input id="input" placeholder="Ask something..." 
                style="flex:1;padding:10px;border:none;outline:none;background:#1e293b;color:white;">
            <button id="send" style="padding:10px;background:#22c55e;border:none;color:white;">
                Send
            </button>
        </div>
    `;

    document.body.appendChild(container);

    const input = document.getElementById("input");
    const send = document.getElementById("send");
    const messages = document.getElementById("messages");

    function addMessage(text, align="left") {
        const msg = document.createElement("div");
        msg.style.marginBottom = "8px";
        msg.style.textAlign = align;
        msg.innerText = text;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    send.onclick = async function() {
        const question = input.value;
        if (!question) return;

        addMessage(question, "right");
        input.value = "";

        const res = await fetch("https://api.piroxeno.com/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": "58BElXh6UG6P9J5txHzDQfl_xOyqPyCSykJ_fYUS28Q"
            },
            body: JSON.stringify({ question })
        });

        const data = await res.json();
        addMessage(data.answer);
    };

    window.PiroxenoWidget = true;
})();
"""
    return Response(content=js_code, media_type="application/javascript")