"""
pages/2_Supplier_Login.py — Meridian Match Supplier Login Page

Handles supplier authentication (login + signup).
Displays demo credentials prominently for evaluators.
Redirects to the Supplier Portal on successful login.
"""

import streamlit as st
from core.database import init_db
from core.auth import login, signup
from theme import inject_css, logo_html

st.set_page_config(
    page_title="Supplier Login — Meridian Match",
    page_icon="🏭",
    layout="centered",
)

init_db()
inject_css()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(logo_html("1.4rem"), unsafe_allow_html=True)
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.page_link("app.py",                    label="🏠 Home")
    st.page_link("pages/1_Client_Login.py",   label="🛒 Client Login")
    st.page_link("pages/2_Supplier_Login.py", label="🏭 Supplier Login")
    st.page_link("pages/5_Admin_Dashboard.py",label="⚙️ Admin Dashboard")

# ── If already logged in as supplier, redirect ────────────────────────────────
if st.session_state.get("logged_in") and st.session_state.get("role") == "supplier":
    st.success("You are already logged in as a supplier.")
    if st.button("Go to Supplier Portal →"):
        st.switch_page("pages/4_Supplier_Portal.py")
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-family:\"Playfair Display\",serif;color:#1B4332;'>Supplier Login</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-family:Inter,sans-serif;color:#52796F;'>Access your supplier portal to list your offerings and view matched client requirements.</p>",
    unsafe_allow_html=True,
)

# ── Demo credentials info box ─────────────────────────────────────────────────
st.markdown(
    """
    <div class='bb-info-box'>
        <strong>🔑 Demo Access — use these credentials to explore</strong><br>
        <span style='font-family:monospace;font-size:0.9rem;'>
        supplier1 / supplier123<br>
        supplier2 / supplier123<br>
        supplier3 / supplier123<br>
        supplier4 / supplier123<br>
        supplier5 / supplier123
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs: Login / Sign Up ─────────────────────────────────────────────────────
tab_login, tab_signup = st.tabs(["🔑 Login", "✏️ Create Account"])

with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("supplier_login_form"):
        username = st.text_input("Username", placeholder="e.g. supplier1")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Login →", use_container_width=True)

    if submitted:
        if not username or not password:
            st.markdown(
                "<div class='bb-warn-box'>⚠️ Please enter both username and password.</div>",
                unsafe_allow_html=True,
            )
        else:
            user = login(username.strip(), password)
            if user is None:
                st.markdown(
                    "<div class='bb-warn-box'>❌ Invalid username or password.</div>",
                    unsafe_allow_html=True,
                )
            elif user["role"] != "supplier":
                st.markdown(
                    "<div class='bb-warn-box'>❌ This account is not a supplier account. "
                    "Please use the Client Login page.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.session_state["logged_in"]  = True
                st.session_state["role"]       = "supplier"
                st.session_state["user_id"]    = user["id"]
                st.session_state["username"]   = user["username"]
                st.session_state["linked_id"]  = user["linked_id"]
                st.markdown(
                    "<div class='bb-success-box'>✅ Login successful! Redirecting…</div>",
                    unsafe_allow_html=True,
                )
                st.switch_page("pages/4_Supplier_Portal.py")

with tab_signup:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.9rem;color:#52796F;'>Create a new supplier account. You'll fill in your product offerings in the portal.</p>",
        unsafe_allow_html=True,
    )
    with st.form("supplier_signup_form"):
        new_username = st.text_input("Choose a Username", placeholder="e.g. gujarat_textiles")
        new_password = st.text_input(
            "Choose a Password",
            type="password",
            placeholder="Minimum 6 characters",
        )
        confirm_pw   = st.text_input("Confirm Password", type="password")
        signup_btn   = st.form_submit_button("Create Account →", use_container_width=True)

    if signup_btn:
        if new_password != confirm_pw:
            st.markdown(
                "<div class='bb-warn-box'>⚠️ Passwords do not match.</div>",
                unsafe_allow_html=True,
            )
        else:
            ok, msg, uid = signup(new_username, new_password, "supplier")
            if ok:
                st.markdown(
                    f"<div class='bb-success-box'>✅ {msg} You can now log in.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='bb-warn-box'>❌ {msg}</div>",
                    unsafe_allow_html=True,
                )
