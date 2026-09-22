"""
theme.py — Meridian Match Shared Design System

Injected CSS theme with exact color palette:
  - Forest Green (primary):     #1B4332
  - Sage Green (secondary):     #52796F
  - Cream (background):         #F5F1E3
  - Warm White (cards/panels):  #FDFBF6
  - Deep Red (accent/CTA):      #9B2C2C
  - Muted Gold (highlights):    #C9A227
  - Charcoal (text):            #2B2B2B
Typography: Playfair Display for headings, Inter for body text.
"""

import html

FOREST_GREEN = "#1B4332"
SAGE_GREEN   = "#52796F"
CREAM        = "#F5F1E3"
WARM_WHITE   = "#FDFBF6"
DEEP_RED     = "#9B2C2C"
MUTED_GOLD   = "#C9A227"
CHARCOAL     = "#2B2B2B"

CATEGORIES = [
    "Textiles & Apparel",
    "Electronics & Components",
    "Food & Beverage",
    "Packaging Materials",
    "Furniture & Fixtures",
    "Industrial Equipment",
    "Office & Stationery Supplies",
    "Construction Materials",
    "Chemicals & Raw Materials",
    "Agricultural Products",
]

QUANTITY_UNITS = ["units", "kg", "tons", "boxes", "liters"]

LOCATION_STATES: dict[str, str] = {
    # Maharashtra / MMR
    "Mumbai": "Maharashtra",
    "Navi Mumbai": "Maharashtra",
    "Kharghar": "Maharashtra",
    "Thane": "Maharashtra",
    "Kalyan": "Maharashtra",
    "Pune": "Maharashtra",
    "Nagpur": "Maharashtra",
    "Nashik": "Maharashtra",
    "Aurangabad": "Maharashtra",
    "Chhatrapati Sambhajinagar": "Maharashtra",
    "Kolhapur": "Maharashtra",
    "Solapur": "Maharashtra",
    # Delhi NCR / North
    "Delhi": "Delhi",
    "New Delhi": "Delhi",
    "Noida": "Uttar Pradesh",
    "Greater Noida": "Uttar Pradesh",
    "Ghaziabad": "Uttar Pradesh",
    "Gurgaon": "Haryana",
    "Gurugram": "Haryana",
    "Faridabad": "Haryana",
    "Panipat": "Haryana",
    "Chandigarh": "Chandigarh",
    "Mohali": "Punjab",
    "Ludhiana": "Punjab",
    "Amritsar": "Punjab",
    "Jalandhar": "Punjab",
    "Dehradun": "Uttarakhand",
    "Haridwar": "Uttarakhand",
    "Jaipur": "Rajasthan",
    "Jodhpur": "Rajasthan",
    "Udaipur": "Rajasthan",
    "Kota": "Rajasthan",
    # Uttar Pradesh / Bihar / Central
    "Lucknow": "Uttar Pradesh",
    "Kanpur": "Uttar Pradesh",
    "Agra": "Uttar Pradesh",
    "Varanasi": "Uttar Pradesh",
    "Prayagraj": "Uttar Pradesh",
    "Meerut": "Uttar Pradesh",
    "Bareilly": "Uttar Pradesh",
    "Aligarh": "Uttar Pradesh",
    "Patna": "Bihar",
    "Gaya": "Bihar",
    "Bhopal": "Madhya Pradesh",
    "Indore": "Madhya Pradesh",
    "Gwalior": "Madhya Pradesh",
    "Jabalpur": "Madhya Pradesh",
    "Raipur": "Chhattisgarh",
    "Ranchi": "Jharkhand",
    "Jamshedpur": "Jharkhand",
    # Gujarat / West
    "Ahmedabad": "Gujarat",
    "Surat": "Gujarat",
    "Vadodara": "Gujarat",
    "Rajkot": "Gujarat",
    "Gandhinagar": "Gujarat",
    "Bhavnagar": "Gujarat",
    # Karnataka / South
    "Bengaluru": "Karnataka",
    "Mysuru": "Karnataka",
    "Mangaluru": "Karnataka",
    "Hubballi": "Karnataka",
    "Belagavi": "Karnataka",
    # Tamil Nadu
    "Chennai": "Tamil Nadu",
    "Coimbatore": "Tamil Nadu",
    "Madurai": "Tamil Nadu",
    "Tiruppur": "Tamil Nadu",
    "Salem": "Tamil Nadu",
    "Tiruchirappalli": "Tamil Nadu",
    # Telangana & Andhra Pradesh
    "Hyderabad": "Telangana",
    "Warangal": "Telangana",
    "Visakhapatnam": "Andhra Pradesh",
    "Vijayawada": "Andhra Pradesh",
    "Guntur": "Andhra Pradesh",
    "Tirupati": "Andhra Pradesh",
    # Kerala
    "Kochi": "Kerala",
    "Thiruvananthapuram": "Kerala",
    "Kozhikode": "Kerala",
    # East / North-East
    "Kolkata": "West Bengal",
    "Howrah": "West Bengal",
    "Durgapur": "West Bengal",
    "Siliguri": "West Bengal",
    "Bhubaneswar": "Odisha",
    "Cuttack": "Odisha",
    "Rourkela": "Odisha",
    "Guwahati": "Assam",
    # Fallback
    "Other": "Other",
}

LOCATIONS: list[str] = sorted([k for k in LOCATION_STATES.keys() if k != "Other"]) + ["Other"]


def inject_css() -> None:
    """Inject Meridian Match custom CSS styling across all Streamlit components."""
    import streamlit as st

    css = (
        "<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
        "<link href='https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700"
        "&family=Inter:wght@300;400;500;600&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"
        "&display=swap' rel='stylesheet'>"
        "<style>"
        ":root{"
        "--forest:#1B4332;--sage:#52796F;--cream:#F5F1E3;"
        "--warm:#FDFBF6;--red:#9B2C2C;--gold:#C9A227;--charcoal:#2B2B2B;"
        "}"
        "html,body,[data-testid='stAppViewContainer'],[data-testid='stMain']{"
        "background-color:var(--cream)!important;color:var(--charcoal)!important;"
        "font-family:'Inter',sans-serif!important;}"
        "h1,h2,h3,.bb-heading{font-family:'Playfair Display',serif!important;color:var(--forest)!important;}"
        "h4,h5,h6{font-family:'Inter',sans-serif!important;color:var(--sage)!important;}"
        ".stButton>button{background-color:var(--red)!important;color:#fff!important;"
        "border:none!important;border-radius:8px!important;font-family:'Inter',sans-serif!important;"
        "font-weight:600!important;padding:0.55rem 1.4rem!important;transition:all 0.2s ease!important;}"
        ".stButton>button:hover{background-color:#7B1F1F!important;color:#fff!important;}"
        ".stTextInput input,.stTextArea textarea,.stNumberInput input,.stSelectbox [data-baseweb='select']{"
        "background-color:var(--warm)!important;border:1px solid #C8C0A8!important;"
        "border-radius:6px!important;color:var(--charcoal)!important;}"
        ".bb-card{background:var(--warm);border-radius:14px;padding:1.3rem 1.5rem;"
        "margin-bottom:1rem;box-shadow:0 2px 8px rgba(27,67,50,0.08);border-left:4px solid var(--sage);color:var(--charcoal)!important;}"
        ".bb-card-highlight{border-left-color:var(--gold)!important;}"
        ".bb-card-alert{border-left-color:var(--red)!important;}"
        ".bb-badge{display:inline-block;background:var(--gold);color:var(--forest);"
        "font-family:'Playfair Display',serif;font-weight:700;font-size:1rem;"
        "padding:0.25rem 0.85rem;border-radius:999px;margin-bottom:0.3rem;}"
        ".bb-bar-wrap{background:#E8E2D0;border-radius:999px;height:9px;width:100%;margin:3px 0 8px;}"
        ".bb-bar-fill{height:9px;border-radius:999px;"
        "background:linear-gradient(90deg,var(--sage),var(--gold));transition:width 0.4s ease;}"
        ".bb-notif-badge{display:inline-block;background:var(--red);color:#fff;font-size:0.65rem;"
        "font-weight:700;border-radius:999px;padding:1px 6px;vertical-align:super;}"
        ".bb-info-box{background:#E8F0EE;border:1px solid var(--sage);border-radius:10px;"
        "padding:0.9rem 1.1rem;margin-bottom:1rem;font-size:0.92rem;color:var(--charcoal)!important;}"
        ".bb-warn-box{background:#FDF3F3;border:1px solid var(--red);border-radius:10px;"
        "padding:0.9rem 1.1rem;margin-bottom:1rem;color:var(--red)!important;font-size:0.92rem;}"
        ".bb-success-box{background:#EDF7F0;border:1px solid var(--sage);border-radius:10px;"
        "padding:0.9rem 1.1rem;margin-bottom:1rem;color:var(--forest)!important;font-size:0.92rem;}"
        ".bb-logo{font-family:'Playfair Display',serif;font-weight:700;color:var(--forest);letter-spacing:-0.5px;}"
        ".bb-logo span{color:var(--gold);}"
        ".bb-tagline{font-family:'Inter',sans-serif;font-size:0.82rem;color:var(--sage);"
        "letter-spacing:0.08em;text-transform:uppercase;margin-top:-0.3rem;}"
        ".bb-kpi{background:var(--warm);border-radius:14px;padding:1.1rem 1.3rem;"
        "text-align:center;box-shadow:0 2px 10px rgba(27,67,50,0.08);color:var(--charcoal)!important;}"
        ".bb-kpi-value{font-family:'Playfair Display',serif;font-size:2.1rem;font-weight:700;color:var(--forest);}"
        ".bb-kpi-label{font-family:'Inter',sans-serif;font-size:0.78rem;color:var(--sage);"
        "text-transform:uppercase;letter-spacing:0.06em;}"
        ".bb-divider{border:none;border-top:1px solid rgba(232,245,233,0.25);margin:1.2rem 0;}"
        ".bb-footer{font-size:0.75rem;color:#9A9280;text-align:center;margin-top:2rem;}"
        "[data-testid='stMetric']{background:var(--warm);border-radius:12px;padding:0.8rem 1rem;}"
        "[data-testid='stMain'] [data-testid='stExpander']{background:var(--warm)!important;border-radius:10px!important;"
        "border:1px solid #D0C8B0!important;color:var(--charcoal)!important;}"
        "[data-testid='stMain'] [data-testid='stExpander'] summary{color:var(--forest)!important;font-weight:600!important;}"
        "[data-testid='stMain'] [data-testid='stExpander'] summary *{color:var(--forest)!important;}"
        "[data-testid='stMain'] [data-testid='stExpander'] [data-testid='stExpanderDetails'],"
        "[data-testid='stMain'] [data-testid='stExpander'] [data-testid='stExpanderDetails'] *{color:var(--charcoal)!important;}"
        "[data-testid='stSidebar']{background-color:var(--forest)!important;}"
        "[data-testid='stSidebar'],"
        "[data-testid='stSidebar'] [data-testid='stMarkdownContainer'],"
        "[data-testid='stSidebar'] [data-testid='stMarkdownContainer'] *,"
        "[data-testid='stSidebar'] p,"
        "[data-testid='stSidebar'] label,"
        "[data-testid='stSidebar'] .stCaption{color:#FDFBF6!important;}"
        "[data-testid='stSidebar'] a,"
        "[data-testid='stSidebar'] a *,"
        "[data-testid='stSidebar'] [data-testid^='stPageLink'],"
        "[data-testid='stSidebar'] [data-testid^='stPageLink'] *,"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink'],"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink'] *,"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink'] p,"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink'] span{color:#FDFBF6!important;text-decoration:none!important;}"
        "[data-testid='stSidebar'] a:hover,"
        "[data-testid='stSidebar'] a:hover *,"
        "[data-testid='stSidebar'] [data-testid^='stPageLink']:hover *,"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink']:hover *,"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink']:hover p,"
        "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink']:hover span{color:var(--gold)!important;}"
        "[data-testid='stSidebar'] .bb-logo{color:#FDFBF6!important;}"
        "[data-testid='stSidebar'] .bb-tagline{color:#A8C5B5!important;}"
        "[data-testid='stSidebar'] .bb-info-box{background:rgba(255,255,255,0.12)!important;border:1px solid rgba(255,255,255,0.22)!important;color:#FDFBF6!important;border-radius:10px;padding:0.85rem;}"
        "[data-testid='stSidebar'] .bb-info-box *{color:#FDFBF6!important;}"
        "[data-testid='stSidebar'] code{color:#FDFBF6!important;background-color:rgba(0,0,0,0.3)!important;"
        "padding:2px 6px!important;border-radius:4px!important;font-weight:600!important;}"
        "[data-testid='stSidebar'] [data-testid='stExpander']{background:rgba(255,255,255,0.08)!important;border:1px solid rgba(255,255,255,0.2)!important;border-radius:10px!important;}"
        "[data-testid='stSidebar'] [data-testid='stExpander'] summary{background:rgba(255,255,255,0.12)!important;color:#FDFBF6!important;font-weight:600!important;border-radius:8px!important;padding:0.45rem 0.75rem!important;}"
        "[data-testid='stSidebar'] [data-testid='stExpander'] summary:hover{background:rgba(255,255,255,0.2)!important;color:var(--gold)!important;}"
        "[data-testid='stSidebar'] [data-testid='stExpander'] summary *{color:#FDFBF6!important;}"
        "[data-testid='stSidebar'] [data-testid='stExpander'] summary:hover *{color:var(--gold)!important;}"
        "[data-testid='stSidebar'] [data-testid='stExpander'] [data-testid='stExpanderDetails'],"
        "[data-testid='stSidebar'] [data-testid='stExpander'] [data-testid='stExpanderDetails'] *{color:#FDFBF6!important;background-color:transparent!important;}"
        "[data-testid='stSidebarNav'],"
        "[data-testid='stSidebarNavItems'],"
        "[data-testid='stSidebarNavSeparator'],"
        "[data-testid='stSidebarHeader'],"
        "[data-testid='stSidebarCollapseButton'],"
        "[data-testid='collapsedControl'],"
        "section[data-testid='stSidebar'] > div:first-child > div:first-child:has(ul),"
        "section[data-testid='stSidebar'] nav,"
        "section[data-testid='stSidebar'] ul[data-testid='stSidebarNavItems']{"
        "display:none!important;visibility:hidden!important;height:0!important;max-height:0!important;padding:0!important;margin:0!important;overflow:hidden!important;}"
        ".material-symbols-rounded,.material-symbols-outlined,.material-icons,[data-testid='stIconMaterial']{"
        "font-family:'Material Symbols Rounded','Material Icons',sans-serif!important;}"
        "</style>"
    )
    st.markdown(css, unsafe_allow_html=True)


def score_bar_html(label: str, score: float, max_score: float = 100.0) -> str:
    """Return an HTML snippet rendering a labelled score bar in the BB style."""
    pct = min(100.0, max(0.0, (score / max_score) * 100))
    return (
        f"<div style='margin-bottom:3px;font-size:0.81rem;color:#52796F;'>"
        f"<b>{label}</b> — {score:.1f}%</div>"
        f"<div class='bb-bar-wrap'><div class='bb-bar-fill' style='width:{pct:.1f}%'></div></div>"
    )


def logo_html(size: str = "2rem") -> str:
    """Return HTML for the Meridian Match logo mark."""
    return (
        f"<div class='bb-logo' style='font-size:{size};'>Meridian <span>Match</span></div>"
        f"<div class='bb-tagline'>Intelligent Supplier Sourcing</div>"
    )


def kpi_card_html(value: str, label: str) -> str:
    """Return HTML for a styled KPI metric card."""
    return (
        f"<div class='bb-kpi'>"
        f"<div class='bb-kpi-value'>{value}</div>"
        f"<div class='bb-kpi-label'>{label}</div>"
        f"</div>"
    )
