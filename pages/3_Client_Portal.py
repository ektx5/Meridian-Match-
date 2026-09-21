"""
pages/3_Client_Portal.py — Meridian Match Client Portal

Post-login portal for clients to submit product requirements,
view AI-matched suppliers with 6-factor breakdowns, and manage notifications.
"""

from __future__ import annotations

import streamlit as st
from core.database import (
    init_db,
    save_or_update_client,
    get_client_by_user,
    get_explanations_for_match,
    get_matches_for_client,
    get_connection,
)
from core.matching_engine import run_matching_for_client
from core.notifications import (
    get_notifications_for_user,
    get_unread_count,
    mark_all_read,
    mark_notification_read,
    create_match_notifications,
)
from theme import inject_css, logo_html, score_bar_html, CATEGORIES, QUANTITY_UNITS, LOCATIONS

st.set_page_config(page_title="Client Portal — Meridian Match", page_icon="📋", layout="wide")
init_db()
inject_css()

if not st.session_state.get("logged_in") or st.session_state.get("role") != "client":
    st.markdown("<div class='bb-warn-box'>🔒 Please log in as a client to access this page.</div>", unsafe_allow_html=True)
    if st.button("Go to Client Login"):
        st.switch_page("pages/1_Client_Login.py")
    st.stop()

user_id = st.session_state["user_id"]
username = st.session_state.get("username", "Client")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(logo_html("1.3rem"), unsafe_allow_html=True)
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)

    unread = get_unread_count(user_id, "client")
    badge = f"<span class='bb-notif-badge'>{unread}</span>" if unread > 0 else ""
    st.markdown(f"<div style='font-size:1.05rem;font-weight:600;color:#FDFBF6;'>🔔 Notifications{badge}</div>", unsafe_allow_html=True)

    if unread > 0 and st.button("Mark all as read", key="mark_all"):
        mark_all_read(user_id, "client")
        st.rerun()

    notifs = get_notifications_for_user(user_id, "client", limit=6)
    if notifs:
        with st.expander("Recent Alerts", expanded=(unread > 0)):
            for n in notifs:
                weight = "font-weight:600;" if not n["is_read"] else ""
                st.markdown(f"<div style='font-size:0.8rem;{weight}padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.15);color:#FDFBF6;'>{n['message']}</div>", unsafe_allow_html=True)
                if not n["is_read"] and st.button("✓ Read", key=f"read_{n['id']}"):
                    mark_notification_read(n["id"])
                    st.rerun()
    else:
        st.markdown("<div style='font-size:0.82rem;color:#A8C5B5;'>No notifications yet.</div>", unsafe_allow_html=True)

    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.page_link("app.py", label="🏠 Home")
    st.markdown(f"<div style='font-size:0.82rem;color:#A8C5B5;margin-top:0.8rem;'>User: <b>{username}</b></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_client"):
        for k in ["logged_in", "role", "user_id", "username", "linked_id"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")

# ── Portal Header ─────────────────────────────────────────────────────────────
st.markdown("<h1 class='bb-heading'>Client Portal</h1>", unsafe_allow_html=True)
client_row = get_client_by_user(user_id)
is_complete = bool(client_row and client_row["profile_complete"])

if not is_complete:
    st.markdown(
        f"<div class='bb-info-box'>👋 <b>Welcome, {username}!</b> Your requirement profile is pending. "
        "Fill out the form below to activate your account and find matching suppliers.</div>",
        unsafe_allow_html=True,
    )

tab_form, tab_matches = st.tabs(["📝 Submit Requirement", "🤝 My Matches"])

# ── Tab 1: Requirement Form ───────────────────────────────────────────────────
with tab_form:
    st.markdown("<h4>Specify Product Requirements</h4>", unsafe_allow_html=True)
    with st.form("client_req_form"):
        c1, c2 = st.columns(2)
        with c1:
            company_name = st.text_input("Company / Client Name *", value=client_row["company_name"] if client_row and client_row["company_name"] else username)
            cat_idx = CATEGORIES.index(client_row["category"]) if client_row and client_row["category"] in CATEGORIES else 0
            category = st.selectbox("Product Category *", CATEGORIES, index=cat_idx)
            loc_idx = LOCATIONS.index(client_row["location"]) if client_row and client_row["location"] in LOCATIONS else 0
            location = st.selectbox("Location (City) *", LOCATIONS, index=loc_idx)

        with c2:
            q_col, u_col = st.columns([2, 1])
            with q_col:
                quantity_required = st.number_input("Quantity Required *", min_value=0.0, value=float(client_row["quantity_required"]) if client_row else 1000.0, step=10.0)
            with u_col:
                u_idx = QUANTITY_UNITS.index(client_row["quantity_unit"]) if client_row and client_row["quantity_unit"] in QUANTITY_UNITS else 0
                quantity_unit = st.selectbox("Unit", QUANTITY_UNITS, index=u_idx)

            b1, b2 = st.columns(2)
            with b1:
                budget_min = st.number_input("Budget Min (₹) *", min_value=0.0, value=float(client_row["budget_min"]) if client_row else 50000.0, step=5000.0)
            with b2:
                budget_max = st.number_input("Budget Max (₹) *", min_value=0.0, value=float(client_row["budget_max"]) if client_row else 150000.0, step=5000.0)

            delivery_days = st.number_input("Delivery Needed Within (days) *", min_value=1, max_value=365, value=int(client_row["delivery_days"]) if client_row and client_row["delivery_days"] else 30)

        product_requirement = st.text_area(
            "Product Requirement (Detailed Description) *",
            value=client_row["product_requirement"] if client_row else "",
            placeholder="e.g. 100% organic cotton t-shirts, bio-washed, pre-shrunk, available in sizes S-XXL...",
            height=110,
        )
        additional_notes = st.text_area(
            "Additional Notes & Constraints (Feeds the AI Constraint Parser)",
            value=client_row["additional_notes"] if client_row else "",
            placeholder="e.g. Must be GOTS certified. ISO 9001 is mandatory. Prefer eco-friendly packaging if possible.",
            height=90,
            help="Keywords like 'must', 'mandatory', 'required', 'only' trigger deal-breakers. 'prefer', 'ideally' trigger nice-to-haves.",
        )
        submitted = st.form_submit_button("🔍 Submit & Find Matches", use_container_width=True)

    if submitted:
        errors = []
        if not company_name.strip(): errors.append("Company Name is required.")
        if quantity_required <= 0: errors.append("Quantity Required must be greater than 0.")
        if budget_min <= 0 or budget_max <= 0: errors.append("Budget Min and Max must be greater than 0.")
        if budget_min > budget_max: errors.append("Budget Min cannot exceed Budget Max.")
        if not product_requirement.strip(): errors.append("Product Requirement description is required.")

        if errors:
            for e in errors:
                st.markdown(f"<div class='bb-warn-box'>⚠️ {e}</div>", unsafe_allow_html=True)
        else:
            with st.spinner("Analyzing requirements and running AI matching engine..."):
                client_id = save_or_update_client(
                    user_id=user_id, company_name=company_name.strip(),
                    product_requirement=product_requirement.strip(), category=category,
                    quantity_required=float(quantity_required), quantity_unit=quantity_unit,
                    budget_min=float(budget_min), budget_max=float(budget_max),
                    location=location, delivery_days=int(delivery_days),
                    additional_notes=additional_notes.strip(),
                )
                st.session_state["linked_id"] = client_id
                matches = run_matching_for_client(client_id)

                # Send notifications for matches > 60
                conn = get_connection()
                try:
                    for m in matches:
                        if m["overall_score"] >= 60:
                            s_row = conn.execute("SELECT user_id FROM suppliers WHERE id=?", (m["supplier_id"],)).fetchone()
                            if s_row:
                                create_match_notifications(
                                    client_id=client_id, supplier_id=m["supplier_id"],
                                    match_id=m["match_id"], score=m["overall_score"],
                                    explanation=m["explanation_text"], client_user_id=user_id,
                                    supplier_user_id=s_row["user_id"],
                                )
                finally:
                    conn.close()

            st.markdown("<div class='bb-success-box'>✅ Profile updated & AI matching complete! View matches below.</div>", unsafe_allow_html=True)
            st.rerun()

# ── Tab 2: My Matches ─────────────────────────────────────────────────────────
with tab_matches:
    if not is_complete or not client_row:
        st.markdown(
            "<div class='bb-card' style='text-align:center;padding:2.5rem;'>"
            "<div style='font-size:2.5rem;'>📭</div>"
            "<h3>No matches yet</h3>"
            "<p style='color:#52796F;'>Please submit your product requirement in the form tab to find matching suppliers.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        matches = get_matches_for_client(client_row["id"])
        if not matches:
            st.markdown("<div class='bb-info-box'>No matching suppliers found yet. Re-run or check back soon!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3>Top {len(matches)} AI-Matched Suppliers</h3>", unsafe_allow_html=True)
            for i, m in enumerate(matches):
                score = m["overall_score"]
                flag = " ⚠️ Constraint Penalty" if m["constraint_penalty_applied"] else ""
                icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📌"

                with st.expander(f"{icon} {m['supplier_name']} — Match Score: {score:.0f}%{flag}", expanded=(i == 0)):
                    c_left, c_right = st.columns([1.2, 1])
                    with c_left:
                        st.markdown(
                            f"<div class='bb-card' style='margin-bottom:0.6rem;'>"
                            f"<b style='font-size:1.1rem;color:#1B4332;'>{m['supplier_name']}</b><br>"
                            f"<span style='font-size:0.85rem;color:#52796F;'>"
                            f"📦 <b>Offered:</b> {m['product_offered']}<br>"
                            f"📍 <b>Location:</b> {m['supplier_location']} | 🚚 <b>Delivery:</b> {m['supplier_delivery']} days<br>"
                            f"💰 <b>Price:</b> ₹{m['price_min']:,.0f} - ₹{m['price_max']:,.0f} / unit | "
                            f"🗂 <b>Available:</b> {m['available_quantity']:,.0f} {m['supplier_unit']}"
                            f"</span></div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"<div class='bb-badge'>Overall Fit: {score:.0f}%</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='bb-bar-wrap'><div class='bb-bar-fill' style='width:{score:.1f}%;'></div></div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size:0.85rem;color:#2B2B2B;margin-top:0.4rem;'>{m['explanation_text']}</div>", unsafe_allow_html=True)

                    with c_right:
                        st.markdown("<b style='font-size:0.85rem;color:#1B4332;'>Multi-Factor Breakdown</b>", unsafe_allow_html=True)
                        factors = [
                            ("🧠 Product Similarity", m["product_fit_score"]),
                            ("🏷 Category Match", m["category_score"]),
                            ("📦 Quantity Fit", m["quantity_score"]),
                            ("💰 Budget Fit", m["budget_score"]),
                            ("🚚 Delivery Timeline", m["delivery_score"]),
                            ("📍 Location Proximity", m["location_score"]),
                        ]
                        st.markdown("".join(score_bar_html(lbl, val) for lbl, val in factors), unsafe_allow_html=True)

                        exps = get_explanations_for_match(m["id"])
                        if exps:
                            st.markdown("<b style='font-size:0.82rem;color:#1B4332;'>Constraint Checks</b>", unsafe_allow_html=True)
                            for e in exps:
                                mark = "✓" if e["satisfied"] else "⚠️"
                                color = "#1B4332" if e["satisfied"] else "#9B2C2C"
                                tag = "Required" if e["constraint_type"] == "deal_breaker" else "Bonus"
                                st.markdown(f"<div style='font-size:0.78rem;color:{color};'>{mark} [{tag}] {e['constraint_text']}</div>", unsafe_allow_html=True)
