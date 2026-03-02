import streamlit as st
import requests
import uuid

# Configuration
API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Furqii Chat Bot", page_icon="🩺", layout="wide")

# ======================
# HELPER FUNCTIONS
# ======================
def fetch_all_sessions():
    """Fetches the list of all previous chat sessions for the sidebar."""
    try:
        # Calls backend get_all_sessions logic
        res = requests.get(f"{API_BASE}/sessions")
        if res.status_code == 200:
            # Backend returns {"sessions": [...]}
            return res.json().get("sessions", [])
    except Exception as e:
        st.sidebar.error(f"Error loading chat list: {e}")
    return []

def fetch_history(session_id):
    """Fetch previous chat messages for a specific session."""
    try:
        # Calls backend load_session_history logic
        res = requests.get(
            f"{API_BASE}/history", 
            headers={"x-session-id": session_id}
        )
        if res.status_code == 200:
            data = res.json()
            # Backend returns {"history": [...]}
            return data.get("history", []) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Could not load history: {e}")
    return []

# ======================
# SESSION STATE INIT
# ======================
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user" not in st.session_state:
    st.session_state.user = None

# ======================
# UI: LOGIN / SIGNUP
# ======================
if not st.session_state.session_id:
    st.title("🩺 Furqii Chat Bot")
    st.caption("WHO-based Medical Assistant (Pinecone RAG + Ollama)")
    
    tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if not username or not password:
                st.error("Please enter credentials.")
            else:
                try:
                    res = requests.post(
                        f"{API_BASE}/login",
                        json={"username": username, "password": password},
                    )
                    data = res.json()
                    if "session_id" in data:
                        st.session_state.session_id = data["session_id"]
                        st.session_state.user = data.get("user", username)
                        # Load history immediately upon login
                        st.session_state.messages = fetch_history(data["session_id"])
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(data.get("error", "Login failed."))
                except Exception as e:
                    st.error(f"❌ Backend not reachable: {e}")

    with tab_signup:
        su_user = st.text_input("New Username", key="su_user")
        su_pass = st.text_input("New Password", type="password", key="su_pass")
        if st.button("Create Account"):
            try:
                res = requests.post(f"{API_BASE}/signup", json={"username": su_user, "password": su_pass})
                if res.status_code == 200:
                    st.success("✅ Account created! Please login.")
                else:
                    st.error(res.json().get("error", "Signup failed."))
            except Exception as e:
                st.error(f"❌ Error: {e}")
    st.stop()

# ======================
# UI: SIDEBAR (CHAT HISTORY LIST)
# ======================
with st.sidebar:
    st.header(f"👤 {st.session_state.user}")
    
    if st.button("➕ New Chat", use_container_width=True):
        # Generate new session ID
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.subheader("💬 Previous Chats")

    # Fetch and display the list of all sessions from MongoDB
    sessions = fetch_all_sessions()
    if sessions:
        for sess in sessions:
            # Create a button for each session title stored in sessions collection
            button_label = f"📄 {sess.get('title', 'Untitled Chat')}"
            if st.button(button_label, key=f"btn_{sess['session_id']}", use_container_width=True):
                st.session_state.session_id = sess['session_id']
                # Load history for the selected session
                st.session_state.messages = fetch_history(sess['session_id'])
                st.rerun()
    else:
        st.caption("No previous chats found.")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

# ======================
# UI: MAIN CHAT INTERFACE
# ======================
st.title("🩺 Medical Assistant")
st.markdown(f"**Active Session:** `{st.session_state.session_id}`")

# Render Messages with Robust Error Handling
for msg in st.session_state.messages:
    if isinstance(msg, dict) and "role" in msg:
        with st.chat_message(msg["role"]):
            st.write(msg.get("content", ""))
    else:
        with st.chat_message("assistant"):
            st.write(str(msg))

# Chat Input
user_input = st.chat_input("Ask a medical question...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    # Don't manually append here if your backend save_message already handles it
    # But for UI immediate feedback, keep it and refresh on result
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("🔍 Consulting WHO Evidence..."):
        try:
            res = requests.post(
                f"{API_BASE}/ask",
                headers={"x-session-id": st.session_state.session_id},
                json={"question": user_input},
                timeout=120
            )
            data = res.json()
            answer = data.get("answer") or data.get("error") or "No response from AI."
        except Exception as e:
            answer = f"❌ Error: {e}"

    with st.chat_message("assistant"):
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})