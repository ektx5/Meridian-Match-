"""
seed_data.py -- Meridian Match Database Seeder

Populates the database with:
  - 1 admin account
  - 5 demo client accounts (client1–client5 / client123)
  - 5 demo supplier accounts (supplier1–supplier5 / supplier123)
  - 17 realistic client requirement records across all 10 categories
  - 18 realistic supplier offering records
  - Deliberately engineered variety:
      * Strong matches across all factors
      * Good product fit but failing deal-breaker constraints
      * Category overlap with poor budget/quantity fit
  - Full matching engine run at the end

Run with: python seed_data.py
"""

import os
import sys

# ── Ensure project root is on path ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import init_db, get_connection
from core.auth import hash_password
from core.matching_engine import run_full_matching


def _exec(conn, sql: str, params: tuple = ()) -> int:
    """Execute a parameterized INSERT and return lastrowid."""
    cur = conn.execute(sql, params)
    return cur.lastrowid


def seed() -> None:
    """Main seeding function -- safe to call multiple times (uses INSERT OR IGNORE)."""
    # Ensure stdout handles Unicode on Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    init_db()
    conn = get_connection()

    print("[*] Seeding Bridge & Bloom database...")

    # ── 1. Admin user ──────────────────────────────────────────────────────────
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)",
        ("admin", hash_password("admin123"), "admin"),
    )
    conn.commit()
    print("  [ok] Admin user seeded")

    # ── 2. Demo client users ───────────────────────────────────────────────────
    client_user_ids: list[int] = []
    for i in range(1, 6):
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)",
            (f"client{i}", hash_password("client123"), "client"),
        )
    conn.commit()

    for i in range(1, 6):
        row = conn.execute(
            "SELECT id FROM users WHERE username=?", (f"client{i}",)
        ).fetchone()
        client_user_ids.append(row["id"])
    print(f"  ? {len(client_user_ids)} client users seeded")

    # ── 3. Demo supplier users ─────────────────────────────────────────────────
    supplier_user_ids: list[int] = []
    for i in range(1, 6):
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)",
            (f"supplier{i}", hash_password("supplier123"), "supplier"),
        )
    conn.commit()

    for i in range(1, 6):
        row = conn.execute(
            "SELECT id FROM users WHERE username=?", (f"supplier{i}",)
        ).fetchone()
        supplier_user_ids.append(row["id"])
    print(f"  ? {len(supplier_user_ids)} supplier users seeded")

    # ── 4. Client requirement records ─────────────────────────────────────────
    # 17 records, varied categories/locations, deliberate deal-breaker language

    clients_data = [
        # (user_idx, company_name, product_requirement, category,
        #  qty, unit, bmin, bmax, location, delivery_days, notes)

        # --- Textiles & Apparel ---
        (0,
         "Fabrique India Pvt. Ltd.",
         "We require 100% organic cotton t-shirts for our summer collection. "
         "Pre-washed, shrink-resistant, available in sizes S–XXL.",
         "Textiles & Apparel",
         5000, "units", 150000, 400000, "Mumbai", 30,
         "Supplier must be GOTS certified. ISO 9001 certification is mandatory. "
         "We prefer eco-friendly packaging if available."),

        (1,
         "Denim House Co.",
         "Premium stretch denim fabric, 98% cotton 2% elastane, indigo-dyed, "
         "minimum 10 oz weight, roll length 50m+.",
         "Textiles & Apparel",
         2000, "kg", 500000, 1200000, "Ahmedabad", 45,
         "Only OEKO-TEX Standard 100 certified suppliers. "
         "Ideally local Gujarat suppliers to reduce transit time."),

        # --- Electronics & Components ---
        (2,
         "TechNova Solutions",
         "Microcontroller units (MCU) — STM32 series or equivalent ARM Cortex-M4, "
         "3.3V, 64KB RAM minimum, SMD package.",
         "Electronics & Components",
         10000, "units", 800000, 2500000, "Bengaluru", 20,
         "Components must be RoHS compliant. Counterfeit parts are strictly not acceptable — "
         "only authorized distributors. Prefer suppliers with ISO/TS 16949 quality system."),

        (3,
         "Sparkvolt Industries",
         "High-capacity lithium-ion battery cells 18650 format, 3000mAh+, "
         "2C discharge rate, UL certified.",
         "Electronics & Components",
         50000, "units", 2000000, 6000000, "Pune", 25,
         "Cells must be UL 1642 certified — no exceptions. "
         "UN 38.3 transport test compliance is required."),

        # --- Food & Beverage ---
        (4,
         "Greenleaf Organics",
         "Cold-pressed virgin coconut oil, food-grade, unrefined, for retail packaging. "
         "Glass or BPA-free HDPE bottles preferred.",
         "Food & Beverage",
         3000, "liters", 300000, 750000, "Chennai", 15,
         "Supplier must have FSSAI license. Organic certification (PGS-India or equivalent) "
         "is mandatory. Would be nice if supplier provides USDA Organic certified product."),

        (0,
         "Mumbai Masala Works",
         "Mixed whole spices blend — cloves, cardamom, star anise, cinnamon — "
         "food-safe, cleaned and sorted, 25kg packs.",
         "Food & Beverage",
         500, "kg", 200000, 600000, "Mumbai", 21,
         "FSSAI certification required. Ideally sourced from Kerala or Tamil Nadu farms."),

        # --- Packaging Materials ---
        (1,
         "PackRight Solutions",
         "Corrugated cardboard boxes, 3-ply, customisable print, inner dimensions "
         "30x20x15 cm, load capacity 15kg minimum.",
         "Packaging Materials",
         100000, "boxes", 800000, 2000000, "Delhi", 14,
         "Supplier must use FSC-certified paper stock. "
         "Prefer biodegradable adhesive if possible."),

        (2,
         "EcoWrap India",
         "Biodegradable bubble wrap / void fill made from recycled paper or "
         "mushroom-based materials, industrial roll format.",
         "Packaging Materials",
         5000, "kg", 150000, 400000, "Pune", 20,
         "Must be compostable (certified AS4736 or equivalent). "
         "Ideally zero-plastic supply chain."),

        # --- Furniture & Fixtures ---
        (3,
         "Workspace Interiors Ltd.",
         "Ergonomic office chairs with lumbar support, adjustable armrests, "
         "mesh back, 5-star base, BIFMA certified.",
         "Furniture & Fixtures",
         500, "units", 1500000, 4000000, "Delhi", 40,
         "BIFMA X5.1 certification is mandatory for all chairs. "
         "Prefer suppliers who can handle pan-India delivery."),

        # --- Industrial Equipment ---
        (4,
         "Forge & Metal Pvt. Ltd.",
         "CNC turning centres, 3-axis, chuck diameter 250mm minimum, "
         "spindle speed 4000 RPM+, with auto tool changer.",
         "Industrial Equipment",
         5, "units", 5000000, 15000000, "Coimbatore", 60,
         "Must have CE marking. ISO 9001 supplier required. "
         "Ideally includes 2-year warranty and on-site commissioning."),

        # --- Office & Stationery Supplies ---
        (0,
         "ClearDesk Office Supplies",
         "A4 paper, 80 GSM, white, ream of 500 sheets, for high-volume printing. "
         "Acid-free preferred.",
         "Office & Stationery Supplies",
         50000, "boxes", 3000000, 7000000, "Mumbai", 10,
         "FSC certified paper only. Prefer carbon-neutral delivery logistics."),

        # --- Construction Materials ---
        (1,
         "BuildRight Infrastructure",
         "OPC 53-grade cement, ISI marked, in 50kg bags, for large housing "
         "project — consistent quality batch to batch.",
         "Construction Materials",
         5000, "tons", 15000000, 28000000, "Delhi", 30,
         "ISI mark is mandatory. Supplier must provide batch-wise quality test reports. "
         "BIS licensed manufacturer only."),

        # --- Chemicals & Raw Materials ---
        (2,
         "ChemPure Labs",
         "Isopropyl alcohol (IPA) 99.9% pure, pharmaceutical grade, "
         "in 25-litre HDPE drums.",
         "Chemicals & Raw Materials",
         1000, "liters", 500000, 1500000, "Hyderabad", 15,
         "Must be pharma grade with CoA (Certificate of Analysis). "
         "REACH compliant supplier required — no exceptions. "
         "Would prefer GMP-certified manufacturer."),

        # --- Agricultural Products ---
        (3,
         "FreshHarvest Exports",
         "Alphonso mangoes, Grade A export quality, 2.5–3 kg per dozen box, "
         "Ratnagiri origin preferred.",
         "Agricultural Products",
         100, "tons", 5000000, 12000000, "Mumbai", 7,
         "APEDA registered exporter required. "
         "Pesticide residue testing certificate is mandatory. "
         "Prefer GI-tagged Ratnagiri or Devgad source."),

        # --- Textiles (additional, for variety) ---
        (4,
         "Luxury Linen House",
         "Hotel-quality 100% Egyptian cotton bed sheets, 400 thread count, "
         "white, king size with deep fitted corner.",
         "Textiles & Apparel",
         2000, "units", 400000, 900000, "Delhi", 20,
         "Oeko-Tex certification preferred. Prefer suppliers with export experience."),

        # --- Food & Beverage (budget mismatch scenario) ---
        (0,
         "StarBite Snacks",
         "Potato chips, ready-to-sell, 40g individual packs, salted variety, "
         "for retail distribution.",
         "Food & Beverage",
         200000, "units", 100000, 250000, "Kolkata", 10,
         "FSSAI license is mandatory. Prefer recyclable packaging."),

        # --- Electronics (quantity mismatch scenario) ---
        (1,
         "GadgetHub Retail",
         "USB Type-C charging cables, 1-metre, braided, fast-charge compatible "
         "up to 65W, with OEM packaging.",
         "Electronics & Components",
         500000, "units", 5000000, 12000000, "Delhi", 20,
         "RoHS compliance required. Prefer CE marked product."),
    ]

    client_ids: list[int] = []
    for row in clients_data:
        user_idx = row[0]
        uid = client_user_ids[user_idx]
        # Skip if user already has linked_id pointing to existing row
        existing = conn.execute(
            "SELECT id FROM clients WHERE user_id=? AND company_name=?",
            (uid, row[1]),
        ).fetchone()
        if existing:
            client_ids.append(existing["id"])
            continue
        cid = _exec(
            conn,
            """INSERT INTO clients
               (user_id, company_name, product_requirement, category,
                quantity_required, quantity_unit, budget_min, budget_max,
                location, delivery_days, additional_notes, profile_complete)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
            (uid, row[1], row[2], row[3],
             row[4], row[5], row[6], row[7],
             row[8], row[9], row[10]),
        )
        client_ids.append(cid)

    conn.commit()
    print(f"  ? {len(client_ids)} client requirement records seeded")

    # ── 5. Supplier offering records ──────────────────────────────────────────
    # 18 records — deliberately engineered for varied match outcomes

    suppliers_data = [
        # (user_idx, supplier_name, product_offered, category,
        #  qty, unit, pmin, pmax, location, delivery_days, notes)

        # --- Textiles: STRONG MATCH for Fabrique India (GOTS + organic cotton) ---
        (0,
         "OrganicThreads Pvt. Ltd.",
         "We supply 100% GOTS certified organic cotton t-shirts, knitted and woven fabrics, "
         "pre-washed and pre-shrunk, available in bulk custom colours and sizes S–3XL.",
         "Textiles & Apparel",
         10000, "units", 80, 120, "Mumbai", 21,
         "GOTS certified. ISO 9001 certified. Eco-friendly packaging with recycled cardboard."),

        # --- Textiles: Good product fit but NO GOTS cert (deal-breaker miss) ---
        (1,
         "QuickStitch Manufacturers",
         "Cotton t-shirts in bulk, standard quality, pre-washed, sizes S–XXL. "
         "Can handle large order volumes quickly.",
         "Textiles & Apparel",
         8000, "units", 60, 95, "Surat", 15,
         "BCI cotton sourced. Competitive pricing. No organic certification currently."),

        # --- Textiles: OEKO-TEX certified denim for Denim House ---
        (2,
         "Denim Craft Ahmedabad",
         "Premium stretch denim fabric, 98% cotton 2% spandex, indigo and raw washes, "
         "10.5 oz weight, OEKO-TEX Standard 100 certified, roll length 60m.",
         "Textiles & Apparel",
         5000, "kg", 300, 480, "Ahmedabad", 30,
         "OEKO-TEX Standard 100 certified. Gujarat-based, fast local dispatch. "
         "Sustainable dyeing process."),

        # --- Electronics: RoHS + authorized MCU distributor (strong match for TechNova) ---
        (3,
         "Microchip Direct India",
         "Authorized distributor for STMicroelectronics. Stock of STM32 series MCUs "
         "including Cortex-M4, M7 variants. RoHS 3 compliant, genuine parts with CoC.",
         "Electronics & Components",
         50000, "units", 85, 220, "Bengaluru", 14,
         "RoHS 3 compliant. Authorized STMicro distributor. ISO/TS 16949 quality system. "
         "Anti-counterfeit verification available."),

        # --- Electronics: Good product but NOT authorized (deal-breaker miss for TechNova) ---
        (4,
         "ElecStock Wholesale",
         "Wide range of ARM Cortex MCUs including STM32 and compatible variants, "
         "low MOQ, fast shipping across India.",
         "Electronics & Components",
         20000, "units", 70, 180, "Delhi", 7,
         "Grey market stock sourced. Competitive pricing. No certification documentation. "
         "No authorized distributor status."),

        # --- Electronics: Li-ion cells with UL cert (strong match for Sparkvolt) ---
        (0,
         "PowerCell Technologies",
         "18650 lithium-ion cells, 3200mAh, 2C continuous discharge, UL 1642 and "
         "UN 38.3 transport tested. Grade A Samsung SDI and Panasonic sourced.",
         "Electronics & Components",
         100000, "units", 45, 85, "Pune", 18,
         "UL 1642 certified. UN 38.3 test passed. Sourced from Tier-1 manufacturers. "
         "Authorised distributor with full documentation."),

        # --- Food: FSSAI + Organic (strong match for Greenleaf Organics) ---
        (1,
         "PureCoco Kerala",
         "Cold-pressed virgin coconut oil, unrefined, organic, extracted from fresh coconuts. "
         "Available in glass bottles and BPA-free HDPE. PGS-India certified organic.",
         "Food & Beverage",
         5000, "liters", 120, 185, "Chennai", 10,
         "FSSAI licensed. PGS-India organic certified. USDA Organic certification in process. "
         "Sustainable packaging available."),

        # --- Food: FSSAI but NOT organic (deal-breaker miss for Greenleaf) ---
        (2,
         "CocoTrade Suppliers",
         "Refined and virgin coconut oil in bulk, competitive price. "
         "Suitable for food processing and retail.",
         "Food & Beverage",
         8000, "liters", 80, 130, "Mumbai", 12,
         "FSSAI licensed. No organic certification. Conventionally farmed product."),

        # --- Packaging: FSC certified (strong match for PackRight) ---
        (3,
         "GreenBox Packaging",
         "Custom printed corrugated cardboard boxes, 3-ply and 5-ply, FSC-certified stock, "
         "biodegradable adhesive, any print colour, fast MOQ 10,000 units.",
         "Packaging Materials",
         500000, "boxes", 9, 18, "Delhi", 10,
         "FSC certified. Biodegradable adhesive available. Zero-waste production facility."),

        # --- Packaging: NOT FSC certified (deal-breaker miss for PackRight) ---
        (4,
         "BoxMart India",
         "Standard corrugated boxes in all sizes, high volume, quick delivery. "
         "Unbranded and custom print available.",
         "Packaging Materials",
         1000000, "boxes", 7, 13, "Delhi", 7,
         "No FSC certification. Standard kraft paper stock. Large volume capability."),

        # --- Furniture: BIFMA certified (strong match for Workspace Interiors) ---
        (0,
         "ErgoDesk Furniture",
         "BIFMA X5.1 certified ergonomic office chairs with mesh back, lumbar support, "
         "height-adjustable armrests, synchro tilt mechanism. Pan-India delivery.",
         "Furniture & Fixtures",
         2000, "units", 4500, 7500, "Pune", 35,
         "BIFMA X5.1 certified. ISO 9001 manufacturing. Pan-India logistics partner. "
         "5-year warranty on mechanism."),

        # --- Industrial Equipment: CE marked CNC (strong match for Forge & Metal) ---
        (1,
         "PrecisionCraft Machines",
         "CNC turning centres, 3-axis, 280mm chuck, 5000 RPM spindle, 12-station "
         "auto tool changer. CE marked, includes 2-year warranty and commissioning.",
         "Industrial Equipment",
         20, "units", 1200000, 3500000, "Coimbatore", 55,
         "CE marked. ISO 9001 certified manufacturer. On-site commissioning and training included. "
         "2-year warranty on all components."),

        # --- Office Supplies: FSC paper (strong match for ClearDesk) ---
        (2,
         "PaperPath India",
         "FSC certified A4 80GSM copy paper, acid-free, bright white, reams of 500. "
         "Carbon-neutral delivery within Maharashtra and Delhi NCR.",
         "Office & Stationery Supplies",
         200000, "boxes", 65, 90, "Mumbai", 7,
         "FSC certified. Acid-free. Carbon-neutral logistics partner."),

        # --- Construction: ISI marked cement (strong match for BuildRight) ---
        (3,
         "IndoCem Ltd.",
         "OPC 53-grade cement, ISI marked, BIS licensed, 50kg bags. "
         "Consistent quality with batch-wise test reports. Pan-India dispatch.",
         "Construction Materials",
         20000, "tons", 4000, 5500, "Delhi", 25,
         "BIS licensed. ISI mark holder. Batch test reports provided with every dispatch."),

        # --- Chemicals: CoA + REACH compliant IPA (strong match for ChemPure) ---
        (4,
         "ChemStar Pharma",
         "Isopropyl alcohol 99.9% purity, pharma grade, with full Certificate of Analysis. "
         "REACH compliant, GMP certified facility, 25-litre HDPE drums.",
         "Chemicals & Raw Materials",
         5000, "liters", 600, 1200, "Hyderabad", 12,
         "Pharma grade. REACH compliant. GMP certified facility. Full CoA with every batch."),

        # --- Agricultural: APEDA registered mango exporter (strong match for FreshHarvest) ---
        (0,
         "Konkan Agro Exports",
         "Alphonso mangoes, Ratnagiri and Devgad origin, Grade A export quality, "
         "GI tagged, APEDA registered. Pesticide residue tested, cold chain maintained.",
         "Agricultural Products",
         200, "tons", 55000, 95000, "Mumbai", 5,
         "APEDA registered. GI tag Ratnagiri and Devgad. Pesticide residue test certificate. "
         "Cold storage and reefer transport available."),

        # --- Food: Budget way too HIGH for StarBite (budget mismatch scenario) ---
        (1,
         "SnackCraft Gourmet",
         "Premium artisan potato chips, natural ingredients, hand-cooked, "
         "boutique retail packs 40g and 80g.",
         "Food & Beverage",
         50000, "units", 28, 55, "Kolkata", 8,
         "FSSAI licensed. All-natural ingredients. Premium brand positioning. "
         "Compostable packaging available."),

        # --- Electronics: Small qty supplier for GadgetHub (quantity mismatch) ---
        (2,
         "CableCraft India",
         "USB Type-C braided cables, 1m, 65W fast-charge, CE and RoHS certified. "
         "Custom OEM packaging available.",
         "Electronics & Components",
         50000, "units", 12, 22, "Delhi", 15,
         "RoHS compliant. CE marked. OEM branding available. MOQ 5000 units."),
    ]

    supplier_ids: list[int] = []
    for row in suppliers_data:
        user_idx = row[0]
        uid = supplier_user_ids[user_idx]
        existing = conn.execute(
            "SELECT id FROM suppliers WHERE user_id=? AND supplier_name=?",
            (uid, row[1]),
        ).fetchone()
        if existing:
            supplier_ids.append(existing["id"])
            continue
        sid = _exec(
            conn,
            """INSERT INTO suppliers
               (user_id, supplier_name, product_offered, category,
                available_quantity, quantity_unit, price_min, price_max,
                location, delivery_days, additional_notes, profile_complete)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
            (uid, row[1], row[2], row[3],
             row[4], row[5], row[6], row[7],
             row[8], row[9], row[10]),
        )
        supplier_ids.append(sid)

    conn.commit()
    print(f"  ? {len(supplier_ids)} supplier offering records seeded")

    # ── 6. Link users to their primary client/supplier profiles ───────────────
    for i, uid in enumerate(client_user_ids):
        # Link to the first client record belonging to this user
        row = conn.execute(
            "SELECT id FROM clients WHERE user_id=? ORDER BY id LIMIT 1", (uid,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET linked_id=? WHERE id=?", (row["id"], uid)
            )

    for i, uid in enumerate(supplier_user_ids):
        row = conn.execute(
            "SELECT id FROM suppliers WHERE user_id=? ORDER BY id LIMIT 1", (uid,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET linked_id=? WHERE id=?", (row["id"], uid)
            )

    conn.commit()
    print("  ? User linked_id references updated")
    conn.close()

    # ── 7. Run matching engine ─────────────────────────────────────────────────
    print("  ? Running AI matching engine on all pairs?")
    count = run_full_matching()
    print(f"  ? {count} match pairs computed")

    # ── 8. Generate notifications for seeded matches ──────────────────────────
    print("  ? Generating notifications for high-scoring matches?")
    _seed_notifications()
    print("  ? Notifications seeded")

    print("\n?  Seed complete! Run: streamlit run app.py")
    print("\n?  Demo credentials:")
    print("     Clients:   client1?client5  /  client123")
    print("     Suppliers: supplier1?supplier5  /  supplier123")
    print("     Admin:     admin  /  admin123")


def _seed_notifications() -> None:
    """Generate notifications for all seeded matches that score >= 60."""
    from core.database import get_all_matches, get_connection as gc
    from core.notifications import SCORE_THRESHOLD

    conn = gc()
    try:
        matches = conn.execute(
            "SELECT * FROM matches WHERE overall_score >= ?", (SCORE_THRESHOLD,)
        ).fetchall()

        for m in matches:
            # Get client user_id
            c_user = conn.execute(
                "SELECT u.id FROM users u JOIN clients c ON c.user_id=u.id WHERE c.id=?",
                (m["client_id"],),
            ).fetchone()
            # Get supplier user_id
            s_user = conn.execute(
                "SELECT u.id FROM users u JOIN suppliers s ON s.user_id=u.id WHERE s.id=?",
                (m["supplier_id"],),
            ).fetchone()

            if not c_user or not s_user:
                continue

            score = m["overall_score"]
            explanation = m["explanation_text"] or ""

            # Avoid duplicate notifications
            existing_c = conn.execute(
                "SELECT id FROM notifications WHERE user_id=? AND match_id=? AND user_role='client'",
                (c_user["id"], m["id"]),
            ).fetchone()
            if not existing_c:
                conn.execute(
                    """INSERT INTO notifications (user_role, user_id, match_id, message)
                       VALUES ('client', ?, ?, ?)""",
                    (c_user["id"], m["id"],
                     f"🎉 New match ({score:.0f}%): A supplier matches your requirement. {explanation[:200]}"),
                )

            existing_s = conn.execute(
                "SELECT id FROM notifications WHERE user_id=? AND match_id=? AND user_role='supplier'",
                (s_user["id"], m["id"]),
            ).fetchone()
            if not existing_s:
                conn.execute(
                    """INSERT INTO notifications (user_role, user_id, match_id, message)
                       VALUES ('supplier', ?, ?, ?)""",
                    (s_user["id"], m["id"],
                     f"🎉 New match ({score:.0f}%): A client requirement matches your offering. {explanation[:200]}"),
                )

        conn.commit()
    finally:
        conn.close()


def seed_match_statuses() -> None:
    """Part 4 — Seed realistic Confirmed/Rejected statuses for learning engine training.

    Seeds at least 20 matches with status labels based on score thresholds:
      - overall_score >= 70 → Confirmed (high-score pairs = real success)
      - overall_score <= 40 → Rejected  (low-score pairs = real failure)
      - 40 < score < 70    → left as Pending
    This gives the LogisticRegression meaningful training signal.
    """
    conn = get_connection()
    try:
        matches = conn.execute(
            "SELECT id, overall_score FROM matches ORDER BY overall_score DESC"
        ).fetchall()

        if not matches:
            print("  [skip] No matches found — run seed() first")
            return

        confirmed_count = 0
        rejected_count = 0
        for m in matches:
            score = m["overall_score"]
            mid = m["id"]
            if score >= 70 and confirmed_count < 15:
                conn.execute("UPDATE matches SET status='Confirmed' WHERE id=?", (mid,))
                confirmed_count += 1
            elif score <= 40 and rejected_count < 10:
                conn.execute("UPDATE matches SET status='Rejected' WHERE id=?", (mid,))
                rejected_count += 1

        conn.commit()
        total = confirmed_count + rejected_count
        print(f"  [ok] Seeded {total} match statuses: {confirmed_count} Confirmed, {rejected_count} Rejected")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
    seed_match_statuses()
