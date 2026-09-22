# Meridian Match 🧭
### AI-Powered Client–Supplier Matchmaking Platform

**Meridian Match** is a production-grade, multi-page B2B matchmaking platform built with Python, Streamlit, raw SQLite3, and scikit-learn. It connects commercial buyers and verified suppliers through a **multi-factor AI matching engine**, **explainable scoring algorithms**, and a **rule-based NLP constraint reasoning layer**.

---

## 1. Architecture Overview

Meridian Match follows a modular, decoupled architecture where data flows seamlessly from user input to vector scoring, constraint reasoning, persistence, and reactive notifications.

### Data Flow Diagram

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           STREAMLIT CLIENT (UI)                         │
  │  Landing (app.py) │ Client Portal │ Supplier Portal │ Admin Dashboard   │
  └─────────────┬─────────────────────────────────────────────────▲─────────┘
                │ Form Submissions / Profile Updates              │ Real-Time Matches,
                │ + Category Mismatch Advisory Warning            │ Semantic Bars & KPIs
                ▼                                                 │
  ┌───────────────────────────────────────────────────────────────┴─────────┐
  │                    CORE DATA LAYER (core/database.py)                   │
  │  - Raw SQLite3 with Parameterized Queries (No ORM overhead)             │
  │  - Tables: users, clients, suppliers, matches, explanations,            │
  │    notifications, learned_weights                                       │
  └─────────────┬─────────────────────────────────────────────────▲─────────┘
                │                                                 │
                │ Corpus Descriptions & Attributes                │ Persists Matches,
                ▼                                                 │ Top Terms, Semantics
  ┌───────────────────────────────────────────────────────────────┴─────────┐
  │               AI MATCHING ENGINE (core/matching_engine.py)              │
  │                                                                         │
  │   1. TF-IDF Matrix (1-2 ngrams, sublinear TF) → Cosine Similarity       │
  │   2. Dynamic Adaptive Weights (via core/learning_engine.py):            │
  │      - Product Fit        - Category Match     - Quantity Fit           │
  │      - Budget Overlap     - Delivery Timeline  - Location Proximity     │
  │   3. Top-Terms Extraction (top-k shared features for explainability)    │
  └─────────────┬───────────────────────────┬───────────────────────────────┘
                │                           │
                │ Raw Base Score            │ Unstructured Text
                ▼                           ▼
  ┌───────────────────────────┐  ┌──────────────────────────────────────────┐
  │   NLP CONSTRAINT PARSER   │  │             EMBEDDING ENGINE             │
  │ (core/constraint_parser)  │  │      (core/embedding_engine.py)          │
  │ - Regex & Acronym Engine  │  │ - MiniLM SentenceTransformer Embeddings  │
  │ - Deal-Breaker Penalties  │  │ - Dense Vector Cosine Similarity (Deep   │
  │ - Nice-to-Have Bonuses    │  │   Semantic Score — Informational Layer)  │
  └─────────────┬─────────────┘  └──────────┬───────────────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              │ Adjusted Final Score + Semantic + Top Terms
                              ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │         INTELLIGENT SERVICES & DISPATCH LAYER                           │
  │  - Category Classifier (core/category_classifier.py): TF-IDF + Logistic │
  │    Regression advisory mismatch warning and accuracy metric             │
  │  - Adaptive Weight Learner (core/learning_engine.py): Logistic          │
  │    Regression on Confirmed/Rejected match feedback                      │
  │  - Notifications (core/notifications.py): Deduplicated in-app alerts    │
  │  - Email Service (core/email_service.py): SMTP_SSL match notifications  │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack & Rationale

| Component | Choice | Engineering Rationale |
|---|---|---|
| **UI Framework** | **Streamlit** (v1.32+) | Enables rapid, interactive full-stack Python development without the overhead of maintaining a separate JavaScript/React frontend, API serializers, or client-side state sync. Custom injected CSS (`theme.py`) provides an elegant Forest Green & Cream design system with Google Fonts (*Playfair Display* & *Inter*). |
| **Data Storage** | **SQLite3** (`sqlite3` module) | Zero-setup, self-contained, serverless relational database engine. Accessed entirely via raw parameterized SQL queries for full transparency, ACID guarantees, and zero ORM abstraction overhead. Configured with WAL mode for fast concurrency and schema migrations. |
| **AI / NLP Engine** | **scikit-learn** (`TfidfVectorizer` + `LogisticRegression`) | Provides genuine mathematical NLP representation across the full corpus vocabulary without requiring heavy GPU clusters. Powers TF-IDF cosine similarity, the Category Classifier pipeline, and the feedback-driven Adaptive Weight Learner. |
| **Deep Semantics** | **sentence-transformers** (`all-MiniLM-L6-v2`) | Computes dense vector sentence embeddings for deep semantic similarity beyond lexical token overlap. Integrated as an informational comparison layer with graceful CPU fallback. |
| **Transactional Email** | **smtplib** & **email** (Python stdlib) | Zero-dependency, built-in secure SSL email delivery (`SMTP_SSL`) for instant match dispatch. Gracefully defaults to demo mode when environment variables are unconfigured. |
| **Data Manipulation** | **pandas** & **numpy** | Utilized in the Admin Dashboard for high-performance tabular aggregations, score distribution histograms, cross-validation metrics, and multi-dimensional registry filtering. |
| **Authentication** | **Python `hashlib`** (SHA-256) | Clean, dependency-free credential hashing and session state authorization gating across Client, Supplier, and Admin views. |

---

## 3. AI Matching Approach & Constraint Reasoning

### The 6-Factor Weighted Compatibility Model

Every client requirement and supplier offering is evaluated across six orthogonal commercial dimensions:

$$\text{Base Score} = 0.40 \cdot S_{\text{product}} + 0.15 \cdot S_{\text{category}} + 0.15 \cdot S_{\text{quantity}} + 0.15 \cdot S_{\text{budget}} + 0.10 \cdot S_{\text{delivery}} + 0.05 \cdot S_{\text{location}}$$

1. **Semantic Product Similarity (40%)**: TF-IDF cosine similarity between client requirement descriptions and supplier product offerings.
2. **Category Match (15%)**: 100% for exact sector match; 0% for sector mismatch.
3. **Quantity Alignment (15%)**: Ratio of supplier available capacity to client required volume (capped at 100%; smooth linear degradation when below requirement).
4. **Dual-Path Budget Fit (15%)**: Interval overlap scoring supporting both direct per-unit price ranges and total project budget scaling:
   $$\text{Overlap}(A, B) = \frac{\max(0, \min(A_{\max}, B_{\max}) - \max(A_{\min}, B_{\min}))}{\max(A_{\max}, B_{\max}) - \min(A_{\min}, B_{\min})}$$
5. **Delivery Timeline (10%)**: 100% if supplier lead time $\le$ client deadline; proportional penalty for extended timelines.
6. **Location Proximity (5%)**: 100% for same city; 60% for same state (e.g. Mumbai ↔ Pune); 20% for interstate shipping within India.

### Why TF-IDF + Cosine Similarity is Real Machine Learning / NLP

Unlike naive keyword search (e.g. `substring in text`) which treats all words equally and fails on context, **TF-IDF (Term Frequency–Inverse Document Frequency)** is a statistical learning technique that vectors unstructured text in multidimensional space:
- **Term Frequency (TF)**: Measures frequency of terms in a requirement with sublinear scaling (`sublinear_tf=True`) to prevent repetitive spamming from skewing scores.
- **Inverse Document Frequency (IDF)**: Evaluates term rarity across the entire database corpus. Common words across all suppliers (e.g., *"manufacturing"*, *"supplies"*, *"quality"*) receive low weights, while specific commercial keywords (e.g., *"organic cotton"*, *"microcontroller"*, *"biodegradable"*, *"FSSAI"*) receive high weights.
- **Bigram Range (1, 2)**: Captures compound phrases like *"stainless steel"*, *"lead free"*, and *"cold pressed"*.

### The Constraint Parser: Meaningful AI Reasoning Layer

Beyond raw statistical similarity, commercial procurement requires **prerequisite verification**. The rule-based NLP Constraint Parser (`core/constraint_parser.py`) extracts and enforces commercial conditions from free text:

1. **Trigger Extraction**:
   - **Deal-Breakers**: Detected via regex triggers (`must`, `mandatory`, `required`, `only`, `strictly`, `certification`).
   - **Nice-to-Haves**: Detected via preference triggers (`prefer`, `ideally`, `bonus if`, `nice to have`, `optional`).
2. **Entity & Acronym Validation**: Identifies industry standards (e.g., `GOTS`, `ISO 9001`, `RoHS`, `FSC`, `FSSAI`, `BIFMA`, `CE`, `REACH`, `GMP`, `UL`) and verifies their presence in the supplier's verified capabilities text.
3. **Score Penalties & Bonuses**:
   - **Unmet Deal-Breakers**: Multiplies the entire match score by **`0.40×`** (a 40% penalty multiplier). Even a semantically similar supplier will see their score drop from 85% to 34% if they fail a mandatory certification.
   - **Satisfied Nice-to-Haves**: Adds **`+5` bonus points** (capped at 100%).
4. **Explainability**: Every match produces an itemized explanation record stored in the database, viewable in the portal UI with status check indicators.

---

## 4. Setup & Installation Instructions

Follow these step-by-step instructions to run Meridian Match locally:

### Prerequisites
- **Python 3.10+** installed on your system.
- `git` installed.

### Step 1: Clone the Repository
```bash
git clone https://github.com/ektx5/Meridian-Match-.git
cd Meridian-Match-
```

### Step 2: Create and Activate a Virtual Environment (Recommended)
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS / Linux:
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed the Database
Initialize the SQLite schema, populate 10 user accounts, 17 client requirements, and 18 supplier catalogs, and precompute initial compatibility matches:
```bash
python seed_data.py
```
*Output: Seeds accounts and computes 306 pairwise compatibility scores automatically.*

### Step 5: Launch the Application
```bash
streamlit run app.py
```

Open your browser and navigate to:
**`http://localhost:8501`**

---

## 5. Demo Credentials

The platform comes pre-seeded with test accounts across all roles:

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Client** | `client1` | `client123` | Fabrique India (Textiles & Apparel, GOTS requirement) |
| **Client** | `client2` | `client123` | NexaTech Devices (Electronics, RoHS/ISO 9001) |
| **Client** | `client3` | `client123` | SpiceRoots Organics (Food & Beverage, FSSAI) |
| **Client** | `client4` | `client123` | EcoPack Logistics (Packaging, FSC Certified) |
| **Client** | `client5` | `client123` | Apex Workspaces (Furniture, BIFMA Compliant) |
| **Supplier** | `supplier1` | `supplier123` | OrganicThreads India (GOTS & ISO 9001 Certified) |
| **Supplier** | `supplier2` | `supplier123` | QuickStitch Garments (Low cost, non-certified) |
| **Supplier** | `supplier3` | `supplier123` | SiliconCraft Technologies (RoHS & ISO 9001) |
| **Supplier** | `supplier4` | `supplier123` | PureCoco Kerala (Food manufacturer) |
| **Supplier** | `supplier5` | `supplier123` | GreenWrap Sustainable Packaging (FSC) |
| **Admin** | `admin` | `admin123` | Platform Administrator (KPIs, status updates, full re-match) |

*Note: You can also click **"Create an account"** on the Client or Supplier login pages to test the dynamic signup workflow with incomplete profile detection.*

---

## 6. Email / SMTP Setup

Meridian Match includes built-in email notifications via `smtplib` (`SMTP_SSL`) that fire whenever a newly created match satisfies the `SCORE_THRESHOLD` (≥ 60%).

### Demo Mode (Default)
If no SMTP configuration is present, the platform operates in **Demo Mode**: email attempts log harmlessly to the application console without errors, displaying an `📧 Email not configured (demo mode)` indicator in the portal interface.

### Step-by-Step Configuration for Real Email Delivery

1. **Copy the Environment Template**:
   ```bash
   cp .env.example .env
   ```

2. **Populate `.env` with Your SMTP Credentials**:
   ```ini
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=465
   SMTP_USER=your@email.com
   SMTP_PASS=your_app_password
   ```
   *Note: For Gmail, generate a 16-character **App Password** under Google Account → Security → 2-Step Verification → App passwords.*

3. **Export Variables (or load into your shell / execution environment)**:
   ```bash
   # On Linux/macOS:
   export $(grep -v '^#' .env | xargs)

   # On Windows (PowerShell):
   Get-Content .env | ForEach-Object {
       if ($_ -match '^(.*?)=(.*)$') {
           [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
       }
   }
   ```

4. Provide an email address in the optional **"Notification Email"** input when submitting or updating your profile in either portal.

---

## 7. Future Scalability Roadmap

The platform has progressed significantly from a baseline matching engine to an adaptive, multi-layered intelligent platform. The roadmap below highlights what is now **implemented** versus future architectural enhancements for enterprise scale (100,000+ active records):

### Implemented Upgrades
- [x] **Deep Semantic Similarity Layer (`core/embedding_engine.py`)**: MiniLM (`all-MiniLM-L6-v2`) sentence transformer embeddings running dense vector cosine similarity alongside TF-IDF.
- [x] **Category Classifier & Advisory Validation (`core/category_classifier.py`)**: Multi-class logistic regression on free text to flag potential profile category mismatches before submission.
- [x] **Feedback-Driven Adaptive Weight Learning (`core/learning_engine.py`)**: Machine learning optimization on Confirmed vs. Rejected match statuses to dynamically adjust factor weights.
- [x] **Top-Terms Explainability Engine**: Real-time extraction of overlapping TF-IDF keywords to highlight *why* two businesses align.
- [x] **Secure Transactional Email Dispatch (`core/email_service.py`)**: Out-of-the-box zero-dependency SMTP_SSL notifications.
- [x] **Deduplicated Bidirectional Notifications**: True atomic UPSERT database operations preventing orphaned records or duplicate alerts.

### Future Enterprise Scalability
1. **PostgreSQL + pgvector Migration**:
   - Transition from SQLite to PostgreSQL.
   - Leverage `pgvector` to store 384-dimensional dense vectors with HNSW / IVFFlat indexing for sub-millisecond similarity scans across millions of rows.

2. **Distributed Asynchronous Task Queue (Celery + Redis)**:
   - Offload batch vectorization and re-matching to background workers.
   - Deliver real-time WebSocket push updates to active client sessions.

3. **Enterprise Authentication & Single Sign-On (SSO)**:
   - Implement OAuth2 / SAML authentication, JWT session rotation, and multi-factor authentication (MFA).

4. **Multi-Channel Mobile Messaging**:
   - Integrate WhatsApp Business API and Twilio SMS for real-time mobile match alerts.

---

## 8. License & Assessment Details

Developed for technical evaluation. Built with clean, maintainable, modular Python code.
