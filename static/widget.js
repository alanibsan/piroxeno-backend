(function () {

    if (window.PiroxenoWidget) return;
    window.PiroxenoWidget = true;

    const scriptTag = document.currentScript || document.querySelector('script[data-api-key]');
    const apiKey = scriptTag ? scriptTag.getAttribute("data-api-key") : null;

    if (!apiKey) {
        console.error("Piroxeno: Missing data-api-key attribute.");
        return;
    }

    const API_URL = scriptTag.getAttribute("data-api-url") || "https://api.piroxeno.com";
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

    button.innerHTML = `
        <svg width="26" height="26" viewBox="0 0 24 24" fill="white">
            <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>
        </svg>
    `;

    const panel = document.createElement("div");
    panel.style.position = "fixed";
    panel.style.bottom = "90px";
    panel.style.right = "20px";
    panel.style.width = "360px";
    panel.style.height = "520px";
    panel.style.background = "#0f172a";
    panel.style.border = "0.5px solid rgba(255,255,255,0.08)";
    panel.style.backdropFilter = "blur(12px)";
    panel.style.borderRadius = "20px";
    panel.style.boxShadow = "0 20px 60px rgba(0,0,0,0.5)";
    panel.style.display = "none";
    panel.style.flexDirection = "column";
    panel.style.overflow = "hidden";
    panel.style.zIndex = "9999";

    panel.innerHTML = `
<div style="
padding:16px;
background:#020617;
color:white;
font-weight:600;
display:flex;
align-items:center;
gap:10px;
border-bottom:1px solid rgba(255,255,255,0.08);
">

<div style="
width:8px;
height:8px;
background:#22c55e;
border-radius:50%;
"></div>

Piroxeno Assistant

</div>

<div id="messages" style="
flex:1;
padding:16px;
overflow:auto;
display:flex;
flex-direction:column;
gap:10px;
"></div>

<div style="
display:flex;
padding:12px;
border-top:1px solid rgba(255,255,255,0.08);
gap:8px;
">

<input id="input" placeholder="Ask something..."
style="
flex:1;
padding:10px;
border-radius:8px;
border:none;
outline:none;
background:#020617;
color:white;
">

<button id="send"
style="
padding:10px 14px;
border-radius:8px;
border:none;
background:${PRIMARY_COLOR};
color:white;
cursor:pointer;
">
Send
</button>

</div>

<div style="
font-size:11px;
text-align:center;
padding:6px;
color:#94a3b8;
border-top:1px solid rgba(255,255,255,0.05);
">
Powered by Piroxeno
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

    function addMessage(text, type = "bot") {
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

    async function sendMessage() {

        const question = input.value.trim();
        if (!question) return;

        addMessage(question, "user");
        input.value = "";

        input.disabled = true;
        send.disabled = true;

        const loading = document.createElement("div");
        loading.innerText = "Typing...";
        loading.style.fontSize = "12px";
        loading.style.color = "#94a3b8";
        messages.appendChild(loading);

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-api-key": apiKey
                },
                body: JSON.stringify({ question })
            });

            if (!res.ok) {
                throw new Error("API error");
            }

            const data = await res.json();

            loading.remove();
            addMessage(data.answer || "No response.", "bot");

        } catch (err) {
            loading.remove();
            addMessage("Error connecting to server.", "bot");
        }

        input.disabled = false;
        send.disabled = false;
        input.focus();
    }

    send.onclick = sendMessage;

    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

})();