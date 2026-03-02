/* =========================
   API ENDPOINTS
========================= */
const API_BASE    = "http://127.0.0.1:8000";
const API_LOGIN   = `${API_BASE}/login`;
const API_SIGNUP  = `${API_BASE}/signup`;
const API_ASK     = `${API_BASE}/ask`;
const API_LOGOUT  = `${API_BASE}/logout`;
const API_HISTORY = `${API_BASE}/history`;
const API_RESET   = `${API_BASE}/reset`;


/* =========================
   STATE
========================= */
let sessionId   = localStorage.getItem("session_id") || null;
let username    = localStorage.getItem("username")   || null;
let chatHistory = [];


/* =========================
   SESSION HELPERS
========================= */
function saveSession() {
  if (sessionId) localStorage.setItem("session_id", sessionId);
  if (username)  localStorage.setItem("username",   username);
}

function clearSession() {
  sessionId = null;
  username  = null;
  chatHistory = [];
  localStorage.removeItem("session_id");
  localStorage.removeItem("username");
}


/* =========================
   PAGE SWITCHING
========================= */
function showLogin() {
  document.getElementById("loginPage").classList.remove("hidden");
  document.getElementById("signupPage").classList.add("hidden");
  document.getElementById("chatPage").classList.add("hidden");
}

function showSignup() {
  document.getElementById("loginPage").classList.add("hidden");
  document.getElementById("signupPage").classList.remove("hidden");
  document.getElementById("chatPage").classList.add("hidden");
}

function showChat() {
  document.getElementById("loginPage").classList.add("hidden");
  document.getElementById("signupPage").classList.add("hidden");
  document.getElementById("chatPage").classList.remove("hidden");
  document.getElementById("whoami").innerText =
    username ? `Logged in as ${username}` : "Logged in";
  loadChatHistory();
}


/* =========================
   CHAT RENDERING
========================= */
function restoreChat() {
  const chatBox = document.getElementById("chatBox");
  chatBox.innerHTML = "";
  chatHistory.forEach(m => renderMessage(m.role, m.text));
  chatBox.scrollTop = chatBox.scrollHeight;
}

function renderMessage(role, text) {
  const chatBox = document.getElementById("chatBox");

  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.innerText = role === "bot" ? "🩺" : "🙂";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerText = text;

  if (role === "bot") wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  if (role === "user") wrap.appendChild(avatar);

  chatBox.appendChild(wrap);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function addMessage(role, text) {
  chatHistory.push({ role, text });
  renderMessage(role, text);
}


/* =========================
   LOAD HISTORY FROM BACKEND
========================= */
async function loadChatHistory() {
  if (!sessionId) return;

  try {
    const res = await fetch(API_HISTORY, {
      headers: { "x-session-id": sessionId }
    });

    const data = await res.json();
    if (!data.history) return;

    chatHistory = [];
    data.history.forEach(m => {
      const role = m.role === "assistant" ? "bot" : "user";
      chatHistory.push({ role, text: m.content });
    });

    restoreChat();
  } catch (e) {
    console.log("Could not load history:", e);
  }
}


/* =========================
   THINKING INDICATOR
========================= */
function setThinking(on) {
  const sendBtn = document.querySelector(".send");
  if (sendBtn) sendBtn.disabled = on;

  if (on) {
    addMessage("bot", "Furqii is thinking…");
  }
}

function removeThinking() {
  const last = chatHistory[chatHistory.length - 1];
  if (last && last.role === "bot" && last.text.includes("thinking")) {
    chatHistory.pop();
    restoreChat();
  }
}


/* =========================
   LOGIN
========================= */
async function login() {
  const u   = document.getElementById("username").value.trim();
  const p   = document.getElementById("password").value.trim();
  const msg = document.getElementById("loginMsg");
  msg.innerText = "";

  if (!u || !p) {
    msg.innerText = "⚠️ Please enter username and password.";
    return;
  }

  try {
    const res = await fetch(API_LOGIN, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });

    const data = await res.json();

    if (data.session_id) {
      sessionId = data.session_id;
      username  = data.user || u;
      saveSession();
      showChat();
    } else {
      msg.innerText = "❌ " + (data.error || "Login failed.");
    }
  } catch (e) {
    msg.innerText = "❌ Backend not reachable. Is the server running?";
  }
}


/* =========================
   SIGNUP
========================= */
async function signup() {
  const u   = document.getElementById("su_username").value.trim();
  const p   = document.getElementById("su_password").value.trim();
  const msg = document.getElementById("signupMsg");
  msg.innerText = "";

  if (!u || !p) {
    msg.innerText = "⚠️ Please enter username and password.";
    return;
  }

  try {
    const res = await fetch(API_SIGNUP, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });

    const data = await res.json();

    if (data.message) {
      msg.innerText = "✅ Account created! Please login.";
      setTimeout(() => showLogin(), 1200);
    } else {
      msg.innerText = "❌ " + (data.error || "Signup failed.");
    }
  } catch (e) {
    msg.innerText = "❌ Backend not reachable.";
  }
}


/* =========================
   GOOGLE LOGIN (stub)
   Replace with real Google SDK integration
========================= */
async function googleLogin() {
  alert(
    "Google Login requires Google OAuth setup.\n\n" +
    "1. Create a project at console.developers.google.com\n" +
    "2. Get a CLIENT_ID\n" +
    "3. Integrate Google Identity JS SDK\n" +
    "4. Pass the token to /google-login endpoint"
  );
}


/* =========================
   LOGOUT
========================= */
async function logout() {
  if (sessionId) {
    try {
      await fetch(API_LOGOUT, {
        method: "POST",
        headers: { "x-session-id": sessionId }
      });
    } catch (e) {}
  }

  clearSession();
  showLogin();
}


/* =========================
   NEW CHAT
========================= */
async function newChat() {
  if (sessionId) {
    try {
      await fetch(API_RESET, {
        method: "POST",
        headers: { "x-session-id": sessionId }
      });
    } catch (e) {}
  }

  chatHistory = [];
  restoreChat();
}


/* =========================
   INPUT HELPER
========================= */
function handleEnter(e) {
  if (e.key === "Enter") askQuestion();
}


/* =========================
   ASK QUESTION
========================= */
async function askQuestion() {
  const input = document.getElementById("question");
  const q = input.value.trim();
  if (!q) return;

  if (!sessionId) {
    addMessage("bot", "⚠️ Please login first.");
    return;
  }

  addMessage("user", q);
  input.value = "";
  setThinking(true);

  try {
    const res = await fetch(API_ASK, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-session-id": sessionId
      },
      body: JSON.stringify({ question: q })
    });

    const data = await res.json();
    removeThinking();
    addMessage("bot", data.answer || data.error || "No response received.");
  } catch (e) {
    removeThinking();
    addMessage("bot", "❌ Backend error. Make sure the server is running.");
  }

  setThinking(false);
}


/* =========================
   PAGE LOAD
========================= */
window.onload = () => {
  if (sessionId && username) {
    showChat();
  } else {
    showLogin();
  }
};