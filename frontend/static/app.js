let token = localStorage.getItem("token");
let webcamStream = null;
let captureInterval = null;
let isAnalyzing = false;

document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;

    if (path === "/login" || path === "/") {
        setupLogin();
    } else if (path === "/register") {
        setupRegister();
    } else if (path === "/dashboard") {
        if (!token) window.location.href = "/login";
        else setupDashboard();
    } else if (path === "/history") {
        if (!token) window.location.href = "/login";
        else setupHistory();
    }

    const logoutBtn = document.getElementById("logout");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            localStorage.removeItem("token");
            window.location.href = "/login";
        });
    }
});

function setupLogin() {
    const form = document.getElementById("loginForm");
    if (!form) return;
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const errorEl = document.getElementById("errorMsg");

        try {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem("token", data.access_token);
                window.location.href = "/dashboard";
            } else {
                errorEl.textContent = data.error || "Login failed";
            }
        } catch (err) {
            errorEl.textContent = "Network error";
        }
    });
}

function setupRegister() {
    const form = document.getElementById("registerForm");
    if (!form) return;
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const errorEl = document.getElementById("errorMsg");

        try {
            const res = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem("token", data.access_token);
                window.location.href = "/dashboard";
            } else {
                errorEl.textContent = data.error || "Registration failed";
            }
        } catch (err) {
            errorEl.textContent = "Network error";
        }
    });
}

function setupDashboard() {
    loadDashboardStats();
    setupWebcam();

    document.getElementById("startCam").addEventListener("click", startWebcam);
    document.getElementById("stopCam").addEventListener("click", stopWebcam);
}

async function loadDashboardStats() {
    try {
        const res = await fetch("/api/dashboard", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to load stats");
        const data = await res.json();
        document.getElementById("totalDetections").textContent = data.total_detections;
        document.getElementById("realCount").textContent = data.real_count;
        document.getElementById("fraudCount").textContent = data.fraud_count;
        document.getElementById("suspiciousCount").textContent = data.suspicious_count;
    } catch (err) {
        console.error(err);
    }
}

function setupWebcam() {
    const video = document.getElementById("webcam");
    const startBtn = document.getElementById("startCam");
    const stopBtn = document.getElementById("stopCam");
}

async function startWebcam() {
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById("webcam");
        video.srcObject = webcamStream;
        await video.play();

        document.getElementById("startCam").disabled = true;
        document.getElementById("stopCam").disabled = false;

        isAnalyzing = true;
        captureInterval = setInterval(captureAndAnalyze, 1000);
    } catch (err) {
        alert("Unable to access webcam: " + err.message);
    }
}

function stopWebcam() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
    isAnalyzing = false;
    document.getElementById("startCam").disabled = false;
    document.getElementById("stopCam").disabled = true;

    document.querySelector(".status-indicator").textContent = "⏳ Idle";
    document.getElementById("fraudMeter").style.width = "0%";
    document.getElementById("fraudScore").textContent = "0.00";
    document.getElementById("confidence").textContent = "0.00";
}

function captureAndAnalyze() {
    if (!isAnalyzing) return;
    const video = document.getElementById("webcam");
    if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Image = canvas.toDataURL("image/jpeg", 0.8);
    sendForDetection(base64Image);
}

async function sendForDetection(imageBase64) {
    try {
        const res = await fetch("/api/detect", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ image: imageBase64 })
        });
        if (!res.ok) throw new Error("Detection failed");
        const data = await res.json();

        updateResultDisplay(data);
        loadDashboardStats();
    } catch (err) {
        console.error(err);
    }
}

function updateResultDisplay(result) {
    const statusEl = document.querySelector(".status-indicator");
    const meterEl = document.getElementById("fraudMeter");
    const scoreEl = document.getElementById("fraudScore");
    const confEl = document.getElementById("confidence");

    let statusText = "";
    let color = "";
    if (result.classification === "REAL") {
        statusText = "✅ REAL";
        color = "var(--success)";
    } else if (result.classification === "FAKE") {
        statusText = "⚠️ FAKE";
        color = "var(--danger)";
    } else {
        statusText = "🔍 SUSPICIOUS";
        color = "var(--warning)";
    }

    statusEl.innerHTML = statusText;
    statusEl.style.color = color;
    meterEl.style.width = (result.fraud_score * 100) + "%";
    scoreEl.textContent = result.fraud_score.toFixed(2);
    confEl.textContent = result.confidence.toFixed(2);
}

async function setupHistory() {
    try {
        const res = await fetch("/api/history", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to load history");
        const data = await res.json();
        const tbody = document.getElementById("historyBody");
        const noDataDiv = document.getElementById("noHistory");

        if (data.length === 0) {
            noDataDiv.style.display = "block";
            return;
        }

        noDataDiv.style.display = "none";
        tbody.innerHTML = "";
        data.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${new Date(item.timestamp).toLocaleString()}</td>
                <td>${item.classification}</td>
                <td>${item.fraud_score.toFixed(2)}</td>
                <td>${item.confidence.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (err) {
        console.error(err);
    }
}