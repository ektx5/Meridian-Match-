-- Meridian Match Platform Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('client','supplier','admin')),
    linked_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    company_name TEXT DEFAULT '',
    product_requirement TEXT DEFAULT '',
    category TEXT DEFAULT '',
    quantity_required REAL DEFAULT 0,
    quantity_unit TEXT DEFAULT 'units',
    budget_min REAL DEFAULT 0,
    budget_max REAL DEFAULT 0,
    location TEXT DEFAULT '',
    delivery_days INTEGER DEFAULT 0,
    additional_notes TEXT DEFAULT '',
    profile_complete INTEGER DEFAULT 0,
    notification_email TEXT,
    predicted_category TEXT,
    category_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    supplier_name TEXT DEFAULT '',
    product_offered TEXT DEFAULT '',
    category TEXT DEFAULT '',
    available_quantity REAL DEFAULT 0,
    quantity_unit TEXT DEFAULT 'units',
    price_min REAL DEFAULT 0,
    price_max REAL DEFAULT 0,
    location TEXT DEFAULT '',
    delivery_days INTEGER DEFAULT 0,
    additional_notes TEXT DEFAULT '',
    profile_complete INTEGER DEFAULT 0,
    notification_email TEXT,
    predicted_category TEXT,
    category_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    overall_score REAL NOT NULL,
    product_fit_score REAL NOT NULL,
    category_score REAL NOT NULL,
    quantity_score REAL NOT NULL,
    budget_score REAL NOT NULL,
    delivery_score REAL NOT NULL,
    location_score REAL NOT NULL,
    constraint_penalty_applied INTEGER DEFAULT 0,
    explanation_text TEXT,
    product_fit_semantic_score REAL,
    top_terms TEXT,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Contacted','Confirmed','Rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, supplier_id)
);

CREATE TABLE IF NOT EXISTS match_explanations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    constraint_type TEXT NOT NULL CHECK(constraint_type IN ('deal_breaker','nice_to_have')),
    constraint_text TEXT NOT NULL,
    satisfied INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_role TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    match_id INTEGER REFERENCES matches(id),
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learned_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    computed_at TEXT,
    w_product REAL,
    w_category REAL,
    w_quantity REAL,
    w_budget REAL,
    w_delivery REAL,
    w_location REAL
);
