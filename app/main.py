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

    const PRIMARY_COLOR = "#22c55e";

    const button = document.createElement("div");
    button.style.position = "fixed";
    button.style.bottom = "20px";
    button.style.right = "20px";
    button.style.width = "60px";
    button.style.height = "60px";
    button.style.borderRadius = "50%";
    button.style.background = PRIMARY_COLOR;
    button.style.display = "flex";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.cursor = "pointer";
    button.style.boxShadow = "0 10px 30px rgba(0,0,0,0.4)";
    button.style.zIndex = "9999";
    button.innerHTML = "💬";

    const panel = document.createElement("div");
    panel.style.position = "fixed";
    panel.style.bottom = "90px";
    panel.style.right = "20px";
    panel.style.width = "360px";
    panel.style.height = "520px";
    panel.style.background = "#1e293b";
    panel.style.borderRadius = "16px";
    panel.style.boxShadow = "0 20px 60px rgba(0,0,0,0.5)";
    panel.style.display = "none";
    panel.style.flexDirection = "column";
    panel.style.overflow = "hidden";
    panel.style.zIndex = "9999";

    panel.innerHTML = `
        <div style="padding:15px;background:#0f172a;color:white;font-weight:600;">
            🧠 Piroxeno AI
        </div>
        <div id="messages" style="flex:1;padding:15px;overflow:auto;"></div>
        <div style="display:flex;padding:10px;border-top:1px solid #334155;">
            <input id="input" placeholder="Type your question..."
                style="flex:1;padding:10px;border-radius:8px;border:none;outline:none;background:#0f172a;color:white;">
            <button id="send"
                style="margin-left:8px;padding:10px 14px;border-radius:8px;border:none;background:${PRIMARY_COLOR};color:white;">
                Send
            </button>
        </div>
    `;

    document.body.appendChild(button);
    document.body.appendChild(panel);

    const messages = panel.querySelector("#messages");
    const input = panel.querySelector("#input");
    const send = panel.querySelector("#send");

    button.onclick = () => {
        panel.style.display = panel.style.display === "none" ? "flex" : "none";
    };

    function addMessage(text, type="bot") {
        const bubble = document.createElement("div");
        bubble.style.maxWidth = "75%";
        bubble.style.padding = "10px 14px";
        bubble.style.marginBottom = "10px";
        bubble.style.borderRadius = "14px";
        bubble.style.fontSize = "14px";
        bubble.style.lineHeight = "1.4";

        if (type === "user") {
            bubble.style.background = PRIMARY_COLOR;
            bubble.style.color = "white";
            bubble.style.alignSelf = "flex-end";
            bubble.style.marginLeft = "auto";
        } else {
            bubble.style.background = "#334155";
            bubble.style.color = "white";
        }

        bubble.innerText = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
    }

    send.onclick = async function() {
        const question = input.value.trim();
        if (!question) return;

        addMessage(question, "user");
        input.value = "";

        const loading = document.createElement("div");
        loading.innerText = "Typing...";
        loading.style.fontSize = "12px";
        loading.style.color = "#94a3b8";
        messages.appendChild(loading);

        try {
            const res = await fetch("https://api.piroxeno.com/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-api-key": "58BElXh6UG6P9J5txHzDQfl_xOyqPyCSykJ_fYUS28Q"
                },
                body: JSON.stringify({ question })
            });

            const data = await res.json();
            loading.remove();
            addMessage(data.answer, "bot");

        } catch (err) {
            loading.remove();
            addMessage("Error connecting to server.", "bot");
        }
    };

    window.PiroxenoWidget = true;
})();
"""
    return Response(content=js_code, media_type="application/javascript")