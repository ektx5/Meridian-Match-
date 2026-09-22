"""
pages/4_Supplier_Portal.py — Meridian Match Supplier Portal

Post-login portal for suppliers to submit product offerings,
view matched client requirements with 6-factor breakdowns, and manage notifications.
Includes: semantic score bar, top-terms display, category classifier warning,
email notification on match, UX polish (colored borders, tooltips, empty states).
"""

from __future__ import annotations

import streamlit as st
from core.database import (
    init_db,
    save_or_update_supplier,
    get_supplier_by_user,
    get_explanations_for_match,
    get_matches_for_supplier,
    get_connection,
)
from core.matching_engine import run_matching_for_supplier
from core.notifications import (
    get_notifications_for_user,
    get_unread_count,
    mark_all_read,
    mark_notification_read,
    SCORE_THRESHOLD,
    create_notifications_for_matches,
)
from core.email_service import send_match_email
from theme import inject_css, logo_html, score_bar_html, CATEGORIES, QUANTITY_UNITS, LOCATIONS

st.set_page_config(page_title="Supplier Portal — Meridian Match", page_icon="📦", layout="wide")
init_db()
inject_css()

if not st.session_state.get("logged_in") or st.session_state.get("role") != "supplier":
    st.markdown("<div class='bb-warn-box'>🔒 Please log in as a supplier to access this page.</div>", unsafe_allow_html=True)
    if st.button("Go to Supplier Login"):
        st.switch_page("pages/2_Supplier_Login.py")
    st.stop()

user_id = st.session_state["user_id"]
username = st.session_state.get("username", "Supplier")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(logo_html("1.3rem"), unsafe_allow_html=True)
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)

    unread = get_unread_count(user_id, "supplier")
    badge = f"<span class='bb-notif-badge'>{unread}</span>" if unread > 0 else ""
    st.markdown(f"<div style='font-size:1.05rem;font-weight:600;color:#FDFBF6;'>🔔 Notifications{badge}</div>", unsafe_allow_html=True)

    if unread > 0 and st.button("Mark all as read", key="mark_all_s"):
        mark_all_read(user_id, "supplier")
        st.rerun()

    notifs = get_notifications_for_user(user_id, "supplier", limit=6)
    if notifs:
        with st.expander("Recent Alerts", expanded=(unread > 0)):
            for n in notifs:
                weight = "font-weight:600;" if not n["is_read"] else ""
                st.markdown(f"<div style='font-size:0.8rem;{weight}padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.15);color:#FDFBF6;'>{n['message']}</div>", unsafe_allow_html=True)
                if not n["is_read"] and st.button("✓ Read", key=f"sread_{n['id']}"):
                    mark_notification_read(n["id"])
                    st.rerun()
    else:
        st.markdown("<div style='font-size:0.82rem;color:#A8C5B5;'>No notifications yet.</div>", unsafe_allow_html=True)

    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.page_link("app.py", label="🏠 Home")
    st.markdown(f"<div style='font-size:0.82rem;color:#A8C5B5;margin-top:0.8rem;'>User: <b>{username}</b></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_supplier"):
        for k in ["logged_in", "role", "user_id", "username", "linked_id"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")

# ── Portal Header ─────────────────────────────────────────────────────────────
st.markdown("<h1 class='bb-heading'>Supplier Portal</h1>", unsafe_allow_html=True)
if "portal_status_message" in st.session_state:
    succ, msg = st.session_state.pop("portal_status_message")
    if succ:
        st.markdown(f"<div class='bb-success-box'>✅ {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bb-info-box'>📧 {msg}</div>", unsafe_allow_html=True)

supplier_row = get_supplier_by_user(user_id)
is_complete = bool(supplier_row and supplier_row["profile_complete"])

if not is_complete:
    st.markdown(
        f"<div class='bb-info-box'>👋 <b>Welcome, {username}!</b> Your offering profile is pending. "
        "Fill out the form below to activate your catalog and find matching clients.</div>",
        unsafe_allow_html=True,
    )

tab_form, tab_matches = st.tabs(["📝 List Your Offering", "🤝 My Matches"])

# ── Tab 1: Offering Form ───────────────────────────────────────────────────────
with tab_form:
    st.markdown("<h4>Specify Product Offering & Capabilities</h4>", unsafe_allow_html=True)
    with st.form("supplier_offering_form"):
        c1, c2 = st.columns(2)
        with c1:
            supplier_name = st.text_input("Supplier / Company Name *", value=supplier_row["supplier_name"] if supplier_row and supplier_row["supplier_name"] else username)
            cat_idx = CATEGORIES.index(supplier_row["category"]) if supplier_row and supplier_row["category"] in CATEGORIES else 0
            category = st.selectbox("Product Category *", CATEGORIES, index=cat_idx)
            saved_loc = supplier_row["location"] if supplier_row and supplier_row["location"] else ""
            available_locs = list(LOCATIONS)
            if saved_loc and saved_loc not in available_locs and saved_loc != "Other":
                available_locs.insert(0, saved_loc)
            loc_idx = available_locs.index(saved_loc) if saved_loc in available_locs else 0
            location_sel = st.selectbox("Location (City) *", available_locs, index=loc_idx)
            custom_city = st.text_input(
                "Specify City (if not listed above / Other)",
                value=saved_loc if saved_loc not in LOCATIONS and saved_loc != "Other" else "",
                placeholder="e.g. Kharghar, Navi Mumbai",
            )

        with c2:
            q_col, u_col = st.columns([2, 1])
            with q_col:
                available_quantity = st.number_input("Available Quantity *", min_value=0.0, value=float(supplier_row["available_quantity"]) if supplier_row else 5000.0, step=10.0)
            with u_col:
                u_idx = QUANTITY_UNITS.index(supplier_row["quantity_unit"]) if supplier_row and supplier_row["quantity_unit"] in QUANTITY_UNITS else 0
                quantity_unit = st.selectbox("Unit", QUANTITY_UNITS, index=u_idx)

            p1, p2 = st.columns(2)
            with p1:
                price_min = st.number_input("Price Min (₹/unit) *", min_value=0.0, value=float(supplier_row["price_min"]) if supplier_row else 100.0, step=10.0)
            with p2:
                price_max = st.number_input("Price Max (₹/unit) *", min_value=0.0, value=float(supplier_row["price_max"]) if supplier_row else 250.0, step=10.0)

            delivery_days = st.number_input("Delivery Capability (days) *", min_value=1, max_value=365, value=int(supplier_row["delivery_days"]) if supplier_row and supplier_row["delivery_days"] else 14)

        product_offered = st.text_area(
            "Product Offered (Detailed Description) *",
            value=supplier_row["product_offered"] if supplier_row else "",
            placeholder="e.g. 100% GOTS certified organic cotton garments, bio-washed, customizable colors and bulk capacity...",
            height=110,
        )
        additional_notes = st.text_area(
            "Certifications, Capabilities & Notes (Evaluated by AI Constraint Parser)",
            value=supplier_row["additional_notes"] if supplier_row else "",
            placeholder="e.g. GOTS certified, ISO 9001 registered. Eco-friendly packaging and expedited dispatch available.",
            height=90,
            help="Mention certifications (GOTS, ISO 9001, RoHS, FSSAI, BIFMA) and features (eco-friendly packaging) explicitly.",
        )
        # Part 5 — optional notification email
        notification_email = st.text_input(
            "Notification Email (optional)",
            value=supplier_row["notification_email"] if supplier_row and supplier_row["notification_email"] else "",
            placeholder="you@email.com — receive match alerts by email",
        )
        submitted = st.form_submit_button("🔍 Submit & Find Client Matches", use_container_width=True)

    if submitted:
        location = custom_city.strip() if (location_sel == "Other" or custom_city.strip()) else location_sel
        errors = []
        if not supplier_name.strip(): errors.append("Supplier Name is required.")
        if not location.strip(): errors.append("Location (City) is required.")
        if available_quantity <= 0: errors.append("Available Quantity must be greater than 0.")
        if price_min <= 0 or price_max <= 0: errors.append("Price Min and Max must be greater than 0.")
        if price_min > price_max: errors.append("Price Min cannot exceed Price Max.")
        if not product_offered.strip(): errors.append("Product Offered description is required.")

        if errors:
            for e in errors:
                st.markdown(f"<div class='bb-warn-box'>⚠️ {e}</div>", unsafe_allow_html=True)
        else:
            # Part 3 — category classifier advisory warning
            try:
                from core.category_classifier import train_classifier, predict_category
                from core.database import get_connection as _gc
                _conn = _gc()
                clf_pipeline = train_classifier(_conn)
                _conn.close()
                if clf_pipeline is not None:
                    combined_text = f"{product_offered.strip()} {additional_notes.strip()}"
                    pred_cat, pred_conf = predict_category(combined_text, clf_pipeline)
                    if pred_cat and pred_cat != category and pred_conf > 0.6:
                        st.markdown(
                            f"<div class='bb-warn-box'>⚠️ Our classifier thinks this profile may belong to "
                            f"<b>{pred_cat}</b> (confidence: {pred_conf*100:.0f}%). You selected <b>{category}</b>. "
                            f"If that's intentional, no action needed.</div>",
                            unsafe_allow_html=True,
                        )
            except Exception:
                pred_cat, pred_conf = None, None

            with st.spinner("Analyzing offering and running AI matching engine..."):
                supplier_id = save_or_update_supplier(
                    user_id=user_id, supplier_name=supplier_name.strip(),
                    product_offered=product_offered.strip(), category=category,
                    available_quantity=float(available_quantity), quantity_unit=quantity_unit,
                    price_min=float(price_min), price_max=float(price_max),
                    location=location, delivery_days=int(delivery_days),
                    additional_notes=additional_notes.strip(),
                    notification_email=notification_email.strip() or None,
                )
                st.session_state["linked_id"] = supplier_id
                matches = run_matching_for_supplier(supplier_id)

                # Bug 0.2/0.3 — use deduped create_notifications_for_matches + SCORE_THRESHOLD
                conn = get_connection()
                try:
                    # For supplier portal, notifications need a client_row perspective per match
                    for m in matches:
                        if m["overall_score"] >= SCORE_THRESHOLD:
                            client_db_row = conn.execute("SELECT * FROM clients WHERE id=?", (m["client_id"],)).fetchone()
                            supplier_rows_map = {supplier_id: conn.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,)).fetchone()}
                            if client_db_row:
                                create_notifications_for_matches([m], client_db_row, supplier_rows_map)

                    # Part 5 — send email if configured
                    email_result = None
                    if notification_email.strip():
                        for m in matches:
                            if m["overall_score"] >= SCORE_THRESHOLD:
                                email_result = send_match_email(
                                    to_email=notification_email.strip(),
                                    role="supplier",
                                    match_score=m["overall_score"],
                                    partner_name=m["company_name"],
                                    explanation=m["explanation_text"],
                                    top_terms=m.get("top_terms"),
                                )
                                break
                finally:
                    conn.close()

            if email_result:
                st.session_state["portal_status_message"] = email_result
            else:
                st.session_state["portal_status_message"] = (True, "Catalog updated & AI matching complete! View your matches below.")
            st.rerun()

# ── Tab 2: My Matches ─────────────────────────────────────────────────────────
with tab_matches:
    if not is_complete or not supplier_row:
        # Part 6.2 — empty state
        st.markdown(
            "<div class='bb-info-box' style='text-align:center;padding:2rem;'>"
            "<div style='font-size:2rem;'>📭</div>"
            "<b>No matches yet.</b> Complete your profile and submit to find matching clients."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        matches = get_matches_for_supplier(supplier_row["id"])
        if not matches:
            st.markdown("<div class='bb-info-box'>No matching client requirements found yet. Re-run or check back soon!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3>Top {len(matches)} AI-Matched Client Requirements</h3>", unsafe_allow_html=True)

            for i, m in enumerate(matches):
                score = m["overall_score"]
                flag = " ⚠️ Requirement Missing" if m["constraint_penalty_applied"] else ""
                icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📌"

                # Part 6.3 — color-coded left border
                if score >= 80:
                    border_color = "#C9A227"
                elif score >= 60:
                    border_color = "#52796F"
                elif score < 45:
                    border_color = "#9B2C2C"
                else:
                    border_color = "transparent"

                with st.expander(f"{icon} {m['company_name']} — Match Score: {score:.0f}%{flag}", expanded=(i == 0)):
                    c_left, c_right = st.columns([1.2, 1])
                    with c_left:
                        st.markdown(
                            f"<div class='bb-card' style='margin-bottom:0.6rem;border-left:4px solid {border_color};'>"
                            f"<b style='font-size:1.1rem;color:#1B4332;'>{m['company_name']}</b><br>"
                            f"<span style='font-size:0.85rem;color:#52796F;'>"
                            f"📋 <b>Need:</b> {m['product_requirement']}<br>"
                            f"📍 <b>Location:</b> {m['client_location']} | ⏰ <b>Timeline:</b> {m['client_delivery']} days<br>"
                            f"💰 <b>Budget:</b> ₹{m['budget_min']:,.0f} - ₹{m['budget_max']:,.0f} | "
                            f"🗂 <b>Required:</b> {m['quantity_required']:,.0f} {m['client_unit']}"
                            f"</span></div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"<div class='bb-badge'>Overall Fit: {score:.0f}%</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='bb-bar-wrap'><div class='bb-bar-fill' style='width:{score:.1f}%;'></div></div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size:0.85rem;color:#2B2B2B;margin-top:0.4rem;'>{m['explanation_text']}</div>", unsafe_allow_html=True)

                        # Part 2 — top shared terms
                        top_terms_val = m["top_terms"] if "top_terms" in m.keys() else None
                        if top_terms_val:
                            st.markdown(f"<div style='font-size:0.8rem;color:#52796F;margin-top:0.3rem;'>🔑 Key shared terms: <i>{top_terms_val}</i></div>", unsafe_allow_html=True)

                    with c_right:
                        st.markdown("<b style='font-size:0.85rem;color:#1B4332;'>Multi-Factor Breakdown</b>", unsafe_allow_html=True)
                        factors = [
                            ("🧠 Product Fit",        m["product_fit_score"]),
                            ("🏷 Category Match",     m["category_score"]),
                            ("📦 Quantity Fit",        m["quantity_score"]),
                            ("💰 Budget Fit",          m["budget_score"]),
                            ("🚚 Delivery Timeline",   m["delivery_score"]),
                            ("📍 Location Proximity",  m["location_score"]),
                        ]
                        st.markdown("".join(score_bar_html(lbl, val) for lbl, val in factors), unsafe_allow_html=True)

                        # Part 1 — semantic score bar
                        sem_val = m["product_fit_semantic_score"] if "product_fit_semantic_score" in m.keys() else None
                        if sem_val is not None:
                            st.markdown(score_bar_html("🔬 Deep Semantic Similarity", float(sem_val)), unsafe_allow_html=True)

                        exps = get_explanations_for_match(m["id"])
                        if exps:
                            st.markdown("<b style='font-size:0.82rem;color:#1B4332;'>Client Constraints</b>", unsafe_allow_html=True)
                            for e in exps:
                                mark = "✓" if e["satisfied"] else "⚠️"
                                color = "#1B4332" if e["satisfied"] else "#9B2C2C"
                                tag = "Required" if e["constraint_type"] == "deal_breaker" else "Bonus"
                                st.markdown(f"<div style='font-size:0.78rem;color:{color};'>{mark} [{tag}] {e['constraint_text']}</div>", unsafe_allow_html=True)
