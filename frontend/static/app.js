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

            if (res.ok && data.access_token) {
                localStorage.setItem("token", data.access_token);
                window.location.href = "/dashboard";
            } else {
                errorEl.textContent = data.error || "Login failed";
            }
        } catch (err) {
            console.error(err);
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

            if (res.ok && data.access_token) {
                localStorage.setItem("token", data.access_token);
                window.location.href = "/dashboard";
            } else {
                errorEl.textContent = data.error || "Registration failed";
            }
        } catch (err) {
            console.error(err);
            errorEl.textContent = "Network error";
        }
    });
}

function setupDashboard() {
    loadDashboardStats();

    document.getElementById("startCam").addEventListener("click", startWebcam);
    document.getElementById("stopCam").addEventListener("click", stopWebcam);
}

async function loadDashboardStats() {
    try {
        const res = await fetch("/api/dashboard", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!res.ok) return;

        const data = await res.json();

        document.getElementById("totalDetections").textContent = data.total_detections || 0;
        document.getElementById("realCount").textContent = data.real_count || 0;
        document.getElementById("fraudCount").textContent = data.fraud_count || 0;
        document.getElementById("suspiciousCount").textContent = data.suspicious_count || 0;

    } catch (err) {
        console.error("Dashboard error:", err);
    }
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
        alert("Webcam error: " + err.message);
    }
}

function stopWebcam() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }

    clearInterval(captureInterval);
    isAnalyzing = false;

    document.getElementById("startCam").disabled = false;
    document.getElementById("stopCam").disabled = true;
}

function captureAndAnalyze() {
    if (!isAnalyzing) return;

    const video = document.getElementById("webcam");
    if (!video || video.readyState !== 4) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    const image = canvas.toDataURL("image/jpeg", 0.8);
    sendForDetection(image);
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

        if (!res.ok) return;

        const data = await res.json();

        updateResultDisplay(data);

    } catch (err) {
        console.error("Detection error:", err);
    }
}

function updateResultDisplay(result) {
    if (!result) return;

    const statusEl = document.querySelector(".status-indicator");
    const meterEl = document.getElementById("fraudMeter");
    const scoreEl = document.getElementById("fraudScore");
    const confEl = document.getElementById("confidence");

    const fraudScore = result.fraud_score || 0;
    const confidence = result.confidence || 0;
    const classification = result.classification || "SUSPICIOUS";

    statusEl.textContent = classification;
    meterEl.style.width = (fraudScore * 100) + "%";
    scoreEl.textContent = fraudScore.toFixed(2);
    confEl.textContent = confidence.toFixed(2);
}

async function setupHistory() {
    try {
        const res = await fetch("/api/history", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!res.ok) return;

        const data = await res.json();

        const tbody = document.getElementById("historyBody");
        tbody.innerHTML = "";

        if (!Array.isArray(data) || data.length === 0) {
            return;
        }

        data.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${new Date(item.timestamp).toLocaleString()}</td>
                <td>${item.classification}</td>
                <td>${Number(item.fraud_score || 0).toFixed(2)}</td>
                <td>${Number(item.confidence || 0).toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (err) {
        console.error("History error:", err);
    }
}