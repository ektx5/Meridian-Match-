"""
pages/5_Admin_Dashboard.py — Meridian Match Admin Dashboard

Administrative overview featuring system KPIs, filterable registries,
interactive match status management, analytics charts, and engine re-runs.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
from core.database import (
    init_db,
    get_all_clients,
    get_all_suppliers,
    get_all_matches,
    get_stats,
    update_match_status,
    get_explanations_for_match,
)
from core.matching_engine import run_full_matching
from theme import inject_css, logo_html, kpi_card_html, score_bar_html

st.set_page_config(page_title="Admin Dashboard — Meridian Match", page_icon="⚙️", layout="wide")
init_db()
inject_css()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(logo_html("1.3rem"), unsafe_allow_html=True)
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/1_Client_Login.py", label="🛒 Client Portal")
    st.page_link("pages/2_Supplier_Login.py", label="🏭 Supplier Portal")
    st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='bb-info-box' style='font-size:0.8rem;'>"
        "<b>Admin Demo Credentials:</b><br>User: <code>admin</code><br>Pass: <code>admin123</code></div>",
        unsafe_allow_html=True,
    )

# ── Authentication ─────────────────────────────────────────────────────────────
if not st.session_state.get("admin_logged_in"):
    st.markdown("<h1 class='bb-heading'>Admin Dashboard Login</h1>", unsafe_allow_html=True)
    st.markdown("<div class='bb-info-box'>Use demo credentials: username <code>admin</code>, password <code>admin123</code></div>", unsafe_allow_html=True)
    with st.form("admin_login_box"):
        au = st.text_input("Username")
        ap = st.text_input("Password", type="password")
        if st.form_submit_button("Authenticate →", use_container_width=True):
            if au == "admin" and ap == "admin123":
                st.session_state["admin_logged_in"] = True
                st.rerun()
            else:
                st.markdown("<div class='bb-warn-box'>❌ Invalid credentials.</div>", unsafe_allow_html=True)
    st.stop()

# ── Authenticated View ─────────────────────────────────────────────────────────
top_left, top_right = st.columns([5, 1])
with top_left:
    st.markdown("<h1 class='bb-heading'>Platform Overview & Admin Control</h1>", unsafe_allow_html=True)
with top_right:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Logout Admin"):
        st.session_state.pop("admin_logged_in", None)
        st.rerun()

# ── Top KPIs ──────────────────────────────────────────────────────────────────
stats = get_stats()
k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(kpi_card_html(str(stats["total_clients"]), "Active Clients"), unsafe_allow_html=True)
with k2: st.markdown(kpi_card_html(str(stats["total_suppliers"]), "Active Suppliers"), unsafe_allow_html=True)
with k3: st.markdown(kpi_card_html(str(stats["total_matches"]), "Matches Generated"), unsafe_allow_html=True)
with k4: st.markdown(kpi_card_html(f"{stats['avg_score']:.1f}%", "Average Match Fit"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Live Re-run Bar ────────────────────────────────────────────────────────────
with st.expander("🔄 Re-run Matching Engine Across All Profiles", expanded=False):
    st.write("Recomputes all pairwise compatibility scores using current TF-IDF corpus vocabulary and constraints.")
    if st.button("🚀 Re-calculate All Matches Now"):
        with st.spinner("Executing full matching engine..."):
            count = run_full_matching()
        st.success(f"Successfully computed and stored {count} matches!")
        st.rerun()

st.markdown("<hr class='bb-divider'>", unsafe_allow_html=True)

tab_matches, tab_clients, tab_suppliers, tab_charts = st.tabs(
    ["🤝 Match Management", "🛒 Client Requirements", "🏭 Supplier Offerings", "📊 Analytics & Insights"]
)

# ── Tab 1: Matches ─────────────────────────────────────────────────────────────
with tab_matches:
    matches = get_all_matches()
    if not matches:
        st.info("No matches generated yet. Trigger re-run above.")
    else:
        st.markdown(f"<h4>All System Matches ({len(matches)} pairs)</h4>", unsafe_allow_html=True)
        status_opts = ["Pending", "Contacted", "Confirmed", "Rejected"]

        for m in matches:
            score = m["overall_score"]
            flag = " ⚠️" if m["constraint_penalty_applied"] else ""
            dot = "🟢" if score >= 70 else "🟡" if score >= 45 else "🔴"
            title = f"{dot} {m['company_name']} ↔ {m['supplier_name']} — {score:.0f}%{flag} [{m['status']}]"

            with st.expander(title, expanded=False):
                col_info, col_bars, col_status = st.columns([1.5, 1.5, 1])
                with col_info:
                    st.markdown(f"<div class='bb-badge'>Score: {score:.0f}%</div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size:0.85rem;'>{m['explanation_text']}</p>", unsafe_allow_html=True)

                with col_bars:
                    f_list = [
                        ("Product Fit", m["product_fit_score"]),
                        ("Category", m["category_score"]),
                        ("Quantity", m["quantity_score"]),
                        ("Budget", m["budget_score"]),
                        ("Delivery", m["delivery_score"]),
                        ("Location", m["location_score"]),
                    ]
                    st.markdown("".join(score_bar_html(l, s) for l, s in f_list), unsafe_allow_html=True)
                    exps = get_explanations_for_match(m["id"])
                    for e in exps:
                        c_icon = "✓" if e["satisfied"] else "⚠️"
                        c_color = "#1B4332" if e["satisfied"] else "#9B2C2C"
                        st.markdown(f"<div style='font-size:0.75rem;color:{c_color};'>{c_icon} {e['constraint_text']}</div>", unsafe_allow_html=True)

                with col_status:
                    st.markdown("<b style='font-size:0.8rem;'>Update Match Status</b>", unsafe_allow_html=True)
                    curr_idx = status_opts.index(m["status"]) if m["status"] in status_opts else 0
                    new_status = st.selectbox("Status", status_opts, index=curr_idx, key=f"stat_{m['id']}", label_visibility="collapsed")
                    if new_status != m["status"]:
                        update_match_status(m["id"], new_status)
                        st.rerun()

# ── Tab 2: Clients ─────────────────────────────────────────────────────────────
with tab_clients:
    c_list = get_all_clients()
    if c_list:
        df_c = pd.DataFrame([dict(r) for r in c_list])
        f_cat = st.selectbox("Filter Category", ["All"] + sorted(df_c["category"].unique()), key="fc")
        if f_cat != "All": df_c = df_c[df_c["category"] == f_cat]
        cols = ["id", "company_name", "category", "location", "quantity_required", "quantity_unit", "budget_min", "budget_max", "delivery_days", "profile_complete"]
        st.dataframe(df_c[[c for c in cols if c in df_c.columns]], use_container_width=True, hide_index=True)

# ── Tab 3: Suppliers ───────────────────────────────────────────────────────────
with tab_suppliers:
    s_list = get_all_suppliers()
    if s_list:
        df_s = pd.DataFrame([dict(r) for r in s_list])
        f_scat = st.selectbox("Filter Category", ["All"] + sorted(df_s["category"].unique()), key="fsc")
        if f_scat != "All": df_s = df_s[df_s["category"] == f_scat]
        scols = ["id", "supplier_name", "category", "location", "available_quantity", "quantity_unit", "price_min", "price_max", "delivery_days", "profile_complete"]
        st.dataframe(df_s[[c for c in scols if c in df_s.columns]], use_container_width=True, hide_index=True)

# ── Tab 4: Analytics ───────────────────────────────────────────────────────────
with tab_charts:
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("<h4>Matches per Category</h4>", unsafe_allow_html=True)
        cat_counts = stats.get("matches_per_category", {})
        if cat_counts:
            df_chart = pd.DataFrame(list(cat_counts.items()), columns=["Category", "Matches"]).set_index("Category")
            st.bar_chart(df_chart["Matches"])
    with ch2:
        st.markdown("<h4>Score Distribution</h4>", unsafe_allow_html=True)
        scores = stats.get("score_distribution", [])
        if scores:
            hist, edges = np.histogram(scores, bins=list(range(0, 110, 10)))
            labels = [f"{edges[i]:.0f}-{edges[i+1]:.0f}%" for i in range(len(hist))]
            st.bar_chart(pd.DataFrame({"Score Range": labels, "Count": hist}).set_index("Score Range")["Count"])
