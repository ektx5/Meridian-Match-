"""
app.py — Meridian Match Landing Page

Entry point for the Streamlit multi-page application.
Displays the platform intro, value proposition, and navigation entry points
for Client, Supplier, and Admin users.
"""

import streamlit as st
from core.database import init_db
from theme import inject_css, logo_html, FOREST_GREEN, SAGE_GREEN

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Meridian Match — Intelligent Sourcing",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise DB on every cold start ────────────────────────────────────────
init_db()

# ── Inject design system ──────────────────────────────────────────────────────
inject_css()

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(logo_html("1.6rem"), unsafe_allow_html=True)
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.markdown("**Navigation**")
    st.page_link("app.py",                         label="🏠 Home")
    st.page_link("pages/1_Client_Login.py",         label="🛒 Client Login")
    st.page_link("pages/2_Supplier_Login.py",       label="🏭 Supplier Login")
    st.page_link("pages/3_Client_Portal.py",        label="📋 Client Portal")
    st.page_link("pages/4_Supplier_Portal.py",      label="📦 Supplier Portal")
    st.page_link("pages/5_Admin_Dashboard.py",      label="⚙️ Admin Dashboard")
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.75rem;color:#A8C5B5;'>Meridian Match v1.0</div>",
        unsafe_allow_html=True,
    )

# ── Hero section ──────────────────────────────────────────────────────────────
st.markdown(logo_html("3rem"), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col_hero, col_gap, col_image = st.columns([3, 0.3, 2])

with col_hero:
    st.markdown(
        """
        <div style='font-family:Inter,sans-serif;font-size:0.82rem;font-weight:600;color:#52796F;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem;'>
            AI-Powered Supplier Matchmaking
        </div>
        <h2 style='font-family:"Playfair Display",serif;color:#1B4332;margin-top:0.2rem;line-height:1.2;'>
            Every client has a need.<br>Every supplier has a solution.<br><span style='color:#52796F;'>We find the fit.</span>
        </h2>
        <p style='font-family:Inter,sans-serif;font-size:1.02rem;color:#2B2B2B;max-width:540px;line-height:1.55;margin-top:0.8rem;'>
            Sourcing the right supplier today is manual, slow, and reliant on personal networks or generic directories.
            Meridian Match removes that friction by understanding what a client actually needs and surfacing suppliers
            who are a genuine commercial fit — backed by transparent, explainable match evaluations.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Entry point buttons
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("🛒 I'm a Client", use_container_width=True):
            st.switch_page("pages/1_Client_Login.py")
    with col_b:
        if st.button("🏭 I'm a Supplier", use_container_width=True):
            st.switch_page("pages/2_Supplier_Login.py")
    with col_c:
        if st.button("⚙️ Admin View", use_container_width=True):
            st.switch_page("pages/5_Admin_Dashboard.py")

with col_image:
    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg,{FOREST_GREEN},{SAGE_GREEN});
                    border-radius:20px;padding:2.5rem;text-align:center;margin-top:1rem;'>
            <div style='font-size:4.5rem;margin-bottom:0.8rem;'>🧭</div>
            <div style='font-family:"Playfair Display",serif;color:#FDFBF6;font-size:1.35rem;font-weight:700;'>
                Precision B2B<br>Matchmaking
            </div>
            <div style='font-family:Inter,sans-serif;color:#E8F5E9;font-size:0.88rem;margin-top:0.6rem;line-height:1.6;'>
                Faster sourcing · Fewer mismatches<br>
                Full transparency · Always up to date
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("<br><hr class='bb-divider'>", unsafe_allow_html=True)
st.markdown(
    "<h3 style='font-family:\"Playfair Display\",serif;color:#1B4332;'>How Intelligent Matching Works</h3>",
    unsafe_allow_html=True,
)

steps = [
    ("1️⃣", "Define Your Requirements",
     "Clients submit product specifications, target volumes, budgets, and delivery timelines. "
     "Suppliers list their product catalog, pricing tiers, and production capabilities."),
    ("2️⃣", "Multi-Dimensional Fit Analysis",
     "Our engine analyzes product descriptions, budget boundaries, quantity requirements, "
     "delivery timelines, and geographic proximity together to gauge real-world operational fit."),
    ("3️⃣", "Prerequisite & Compliance Check",
     "Stated constraints — such as mandatory certifications, quality standards, or material preferences — "
     "are evaluated directly, ensuring recommended suppliers meet your non-negotiable requirements."),
    ("4️⃣", "Transparent Match Breakdown",
     "Every match includes factor-by-factor compatibility scores and plain-language summaries "
     "so both parties clearly understand the strengths and fit of each connection."),
]

cols = st.columns(4)
for col, (icon, title, desc) in zip(cols, steps):
    with col:
        st.markdown(
            f"""
            <div class='bb-card'>
                <div style='font-size:2rem;margin-bottom:0.5rem;'>{icon}</div>
                <div style='font-family:"Playfair Display",serif;color:#1B4332;
                            font-size:1rem;font-weight:600;margin-bottom:0.4rem;'>{title}</div>
                <div style='font-family:Inter,sans-serif;font-size:0.85rem;color:#52796F;'>{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Feature highlights ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<h3 style='font-family:\"Playfair Display\",serif;color:#1B4332;'>Platform Highlights</h3>",
    unsafe_allow_html=True,
)

feat_cols = st.columns(3)
features = [
    ("🧠", "Deep Requirement Understanding",
     "Understands full product specifications and domain context to find genuine capabilities "
     "beyond superficial keyword matches."),
    ("🔒", "Deal-Breaker Protection",
     "Verifies non-negotiable standards, certifications, and compliance criteria before "
     "recommending suppliers to buyers."),
    ("📊", "Complete Transparency",
     "Clear factor breakdowns across pricing, volume, timeline, and location provide total visibility "
     "into every match calculation."),
    ("🔔", "Real-Time Match Alerts",
     "Both clients and suppliers receive instant alerts when a high-compatibility match is identified."),
    ("🛡️", "Role-Dedicated Portals",
     "Streamlined dashboards tailored for buyers to specify needs and suppliers to discover commercial demand."),
    ("🔄", "Dynamic Re-Matching",
     "Compatibility scores update automatically as market requirements evolve and new suppliers onboard."),
]

for i, (icon, title, desc) in enumerate(features):
    with feat_cols[i % 3]:
        st.markdown(
            f"""
            <div class='bb-card bb-card-highlight'>
                <span style='font-size:1.5rem;'>{icon}</span>
                <strong style='font-family:"Playfair Display",serif;color:#1B4332;
                               display:block;margin:0.3rem 0;'>{title}</strong>
                <span style='font-size:0.84rem;color:#52796F;font-family:Inter,sans-serif;'>{desc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Demo credentials quick reference ─────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='bb-info-box'>
        <strong>🔑 Quick Demo Access</strong><br>
        <span style='font-size:0.88rem;'>
        <b>Clients:</b> client1/client123 · client2/client123 · client3/client123 · client4/client123 · client5/client123<br>
        <b>Suppliers:</b> supplier1/supplier123 · supplier2/supplier123 · supplier3/supplier123 · supplier4/supplier123 · supplier5/supplier123<br>
        <b>Admin:</b> username <code>admin</code> · password <code>admin123</code>
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='bb-footer'>Meridian Match · Intelligent Client–Supplier Matchmaking Platform</div>",
    unsafe_allow_html=True,
)
