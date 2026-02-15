async function apiHealth() {
    const pill = document.getElementById("statusPill");
    try {
        const res = await fetch("/health");
        if (!res.ok) throw new Error("health not ok");
        const data = await res.json();
        pill.textContent = `API: ${data.status}`;
        pill.style.borderColor = "#34d399";
    } catch (e) {
        pill.textContent = "API: down";
        pill.style.borderColor = "#fb7185";
    }
}

function setError(msg) {
    const box = document.getElementById("errorBox");
    if (!msg) {
        box.hidden = true;
        box.textContent = "";
        return;
    }
    box.hidden = false;
    box.textContent = msg;
}

function setResults(result) {
    document.getElementById("riskValue").textContent = result.risk ?? "—";
    document.getElementById("scoreValue").textContent = (result.score ?? "—").toString();

    const reasonsList = document.getElementById("reasonsList");
    reasonsList.innerHTML = "";
    (result.reasons ?? []).forEach((r) => {
        const li = document.createElement("li");
        li.textContent = r;
        reasonsList.appendChild(li);
    });

    const detWrap = document.getElementById("detectionsList");
    detWrap.innerHTML = "";
    (result.detections ?? []).forEach((d) => {
        const div = document.createElement("div");
        div.className = "detItem";
        div.innerHTML = `
      <div>
        <span class="badge">${escapeHtml(d.label ?? "UNKNOWN")}</span>
        <span class="muted">score:</span> ${escapeHtml(String(d.score ?? ""))}
      </div>
      <div style="margin-top:6px; white-space:pre-wrap;">${escapeHtml(d.span ?? "")}</div>
    `;
        detWrap.appendChild(div);
    });

    const rewrite =
        result.suggested_rewrites && result.suggested_rewrites[0]
            ? result.suggested_rewrites[0]
            : "—";
    document.getElementById("rewriteText").textContent = rewrite;
}

function escapeHtml(s) {
    return s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

async function scan() {
    setError(null);
    const btn = document.getElementById("scanBtn");
    btn.disabled = true;

    const provider = document.getElementById("provider").value;
    const text = document.getElementById("inputText").value.trim();

    if (!text) {
        setError("Please paste some text to scan.");
        btn.disabled = false;
        return;
    }

    try {
        const res = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, provider }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Request failed (${res.status})`);
        }

        const data = await res.json();
        setResults(data);
    } catch (e) {
        setError(e.message || "Unexpected error");
    } finally {
        btn.disabled = false;
    }
}

function clearAll() {
    document.getElementById("inputText").value = "";
    document.getElementById("riskValue").textContent = "—";
    document.getElementById("scoreValue").textContent = "—";
    document.getElementById("reasonsList").innerHTML = "";
    document.getElementById("detectionsList").innerHTML = "";
    document.getElementById("rewriteText").textContent = "—";
    setError(null);
}

async function copyRewrite() {
    const text = document.getElementById("rewriteText").textContent;
    if (!text || text === "—") return;
    await navigator.clipboard.writeText(text);
}

document.getElementById("scanBtn").addEventListener("click", scan);
document.getElementById("clearBtn").addEventListener("click", clearAll);
document.getElementById("copyRewriteBtn").addEventListener("click", copyRewrite);

apiHealth();
