import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Palette (Minimalist Space Mission Control)
    C_BG = RGBColor(11, 15, 25)           # Deep slate navy
    C_CARD = RGBColor(18, 26, 44)         # Card background
    C_CARD_ALT = RGBColor(24, 34, 58)     # Accent card background
    C_CYAN = RGBColor(56, 189, 248)       # Soft cosmic cyan
    C_PURPLE = RGBColor(192, 132, 252)    # Cute lavender purple
    C_GREEN = RGBColor(52, 211, 153)      # Habitable emerald
    C_GOLD = RGBColor(251, 191, 36)       # Warm star gold
    C_CORAL = RGBColor(244, 114, 182)     # Soft coral pink
    C_TEXT = RGBColor(248, 250, 252)      # Pure clean white
    C_MUTED = RGBColor(148, 163, 184)     # Secondary slate

    def apply_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="DBMS CAPSTONE PROJECT"):
        # Category / Pill
        tb_cat = slide.shapes.add_textbox(Inches(0.9), Inches(0.55), Inches(11.5), Inches(0.4))
        p_cat = tb_cat.text_frame.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_CYAN

        # Title
        tb_title = slide.shapes.add_textbox(Inches(0.9), Inches(0.85), Inches(11.5), Inches(0.8))
        p_title = tb_title.text_frame.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = C_TEXT

    def add_card(slide, left, top, width, height, bg_color=C_CARD, border_color=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Cute, Minimalist Space Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_background(s1)

    # Decorative Card Container
    add_card(s1, Inches(1.5), Inches(1.2), Inches(10.333), Inches(5.1), C_CARD, C_CYAN)

    tb1 = s1.shapes.add_textbox(Inches(2.0), Inches(1.8), Inches(9.333), Inches(3.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "🪐 EXOPLANET HABITABILITY CATALOG"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = C_TEXT

    p2 = tf1.add_paragraph()
    p2.text = "A Full-Stack Relational DBMS Architecture & Real-Time Machine Learning Platform"
    p2.font.size = Pt(17)
    p2.font.color.rgb = C_CYAN
    p2.space_before = Pt(14)

    p3 = tf1.add_paragraph()
    p3.text = "Features: 3NF MySQL Normalization • Polyglot NoSQL Telemetry • Automated Confidence Drift Triggers"
    p3.font.size = Pt(13)
    p3.font.color.rgb = C_MUTED
    p3.space_before = Pt(10)

    p4 = tf1.add_paragraph()
    p4.text = "👨‍💻 Group Capstone Defense | Database Management Systems (DBMS)"
    p4.font.size = Pt(13)
    p4.font.bold = True
    p4.font.color.rgb = C_PURPLE
    p4.space_before = Pt(32)

    # =========================================================================
    # SLIDE 2: THE PROBLEM & MOTIVATION
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_background(s2)
    add_header(s2, "The Astronomical Ingestion Challenge & Research Gap")

    # Card 1: The Raw Data Problem
    add_card(s2, Inches(0.9), Inches(1.9), Inches(3.6), Inches(4.7), C_CARD)
    tb = s2.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(3.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🔭 Raw Ingestion Bottleneck"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    items = [
        "Space telescopes (Kepler, TESS) generate massive, disparate CSV exports.",
        "Over 100 raw columns with missing values and sensor noise.",
        "Traditional storage lacks automated schema validation."
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = "• " + it
        p.font.size = Pt(13)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(10)

    # Card 2: The Static Catalog Flaw
    add_card(s2, Inches(4.85), Inches(1.9), Inches(3.6), Inches(4.7), C_CARD)
    tb = s2.shapes.add_textbox(Inches(5.05), Inches(2.1), Inches(3.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📑 The Static Catalog Flaw"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_GOLD
    items = [
        "Conventional databases are passive data stores.",
        "They record raw numbers without calculating habitability.",
        "Astronomers must manually run external scripts to evaluate Earth similarity."
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = "• " + it
        p.font.size = Pt(13)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(10)

    # Card 3: The Research Gap (Our Innovation)
    add_card(s2, Inches(8.8), Inches(1.9), Inches(3.6), Inches(4.7), C_CARD_ALT, C_PURPLE)
    tb = s2.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚡ The Confidence Drift Gap"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE
    items = [
        "Initial planetary measurements have wide error margins.",
        "When revised measurements arrive, standard DBs overwrite silently.",
        "OUR GAP SOLUTION: Automated MySQL triggers that calculate variance and alert researchers when confidence shifts by ≥ 15%!"
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = "• " + it
        p.font.size = Pt(13)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(10)

    # =========================================================================
    # SLIDE 3: 3-TIER ARCHITECTURE OVERVIEW
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_background(s3)
    add_header(s3, "Enterprise 3-Tier System Architecture")

    tiers = [
        ("Tier 1: Presentation (Frontend)", C_CYAN, [
            "Aesthetic Space Mission Control (Glassmorphism UI)",
            "Real-Time Keplerian 2D Canvas Orbit Simulator (T² ∝ a³)",
            "Confidence Drift Radar & Deep Spectroscopy Dossier",
            "Asynchronous Fetch API (Debounced Search & Pagination)"
        ]),
        ("Tier 2: Application (Python / REST API)", C_PURPLE, [
            "Python 3.13 + Flask Modular Blueprint Architecture",
            "Scikit-Learn Random Forest Classifier (200 Estimators)",
            "Custom Decimal-to-Float JSON Serialization Engine",
            "Live NASA TAP (Table Access Protocol) Synchronization"
        ]),
        ("Tier 3: Database (MySQL 8.0 Engine)", C_GREEN, [
            "3NF Relational Decomposition: stars (3,010) ──< exoplanets (4,048)",
            "Automated DML Triggers: trg_after_exoplanet_update",
            "Pre-Compiled Stored Procedures: sp_GetCatalogOverviewStats (< 15ms)",
            "Hybrid NoSQL JSON Document Store: telemetry_json"
        ])
    ]

    for idx, (title, color, bullets) in enumerate(tiers):
        top_pos = Inches(1.9 + idx * 1.7)
        add_card(s3, Inches(0.9), top_pos, Inches(11.5), Inches(1.5), C_CARD, color)
        tb = s3.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.1), Inches(11.1), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = color

        p_desc = tf.add_paragraph()
        p_desc.text = "  •  " + "   |   •  ".join(bullets)
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = C_TEXT
        p_desc.space_before = Pt(6)

    # =========================================================================
    # SLIDE 4: DBMS RELATIONAL SCHEMA & 3NF NORMALIZATION
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_background(s4)
    add_header(s4, "Database Design: 3NF Relational Decomposition")

    # Left: STARS Schema
    add_card(s4, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s4.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⭐ PARENT TABLE: stars (3,010 Records)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    code_stars = [
        "star_id INT AUTO_INCREMENT PRIMARY KEY",
        "name VARCHAR(100) NOT NULL UNIQUE",
        "spectral_type VARCHAR(30) -- e.g. G2 V, M8 V",
        "temperature DECIMAL(10,2) -- Kelvin (K)",
        "radius DECIMAL(10,4)      -- Solar Radii (R☉)",
        "mass DECIMAL(10,4)        -- Solar Masses (M☉)",
        "luminosity DECIMAL(14,6)  -- Solar Luminosity (L☉)",
        "distance_from_earth DECIMAL(12,4) -- Light-Years"
    ]
    for c in code_stars:
        p = tf.add_paragraph()
        p.text = c
        p.font.size = Pt(11)
        p.font.name = "Consolas"
        p.font.color.rgb = C_MUTED
        p.space_before = Pt(4)

    # Right: EXOPLANETS Schema
    add_card(s4, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s4.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🪐 CHILD TABLE: exoplanets (4,048 Records)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    code_planets = [
        "planet_id INT AUTO_INCREMENT PRIMARY KEY",
        "star_id INT NOT NULL -- FOREIGN KEY",
        "name VARCHAR(100) NOT NULL UNIQUE",
        "radius DECIMAL(10,4)     -- Earth Radii (R⊕)",
        "mass DECIMAL(10,4)       -- Earth Masses (M⊕)",
        "predicted_habitability DECIMAL(5,4) -- ML Score",
        "telemetry_json JSON      -- Hybrid NoSQL Doc",
        "CONSTRAINT fk_planet_star FOREIGN KEY (star_id)",
        "  REFERENCES stars(star_id) ON DELETE CASCADE"
    ]
    for c in code_planets:
        p = tf.add_paragraph()
        p.text = c
        p.font.size = Pt(11)
        p.font.name = "Consolas"
        p.font.color.rgb = C_MUTED
        p.space_before = Pt(4)

    p_note = tf.add_paragraph()
    p_note.text = "🔒 ON DELETE CASCADE: Deleting a host star purges orbiting bodies, preventing orphan records."
    p_note.font.size = Pt(11)
    p_note.font.bold = True
    p_note.font.color.rgb = C_GOLD
    p_note.space_before = Pt(12)

    # =========================================================================
    # SLIDE 5: POLYGLOT PERSISTENCE (HYBRID RELATIONAL + JSON)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_background(s5)
    add_header(s5, "Polyglot Persistence: Relational + NoSQL in MySQL 8.0")

    add_card(s5, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s5.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🏛️ Why Polyglot Persistence?"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    points = [
        "Relational Core: Enforces strict ACID compliance and 1-to-many joins between stars and planets.",
        "Document Storage: Space telescopes produce evolving, semi-structured spectroscopic telemetry.",
        "The Solution: Native MySQL JSON document column (telemetry_json) inside the exoplanets entity.",
        "Provides NoSQL flexibility without losing foreign key constraints!"
    ]
    for pt in points:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(12)

    add_card(s5, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD_ALT, C_PURPLE)
    tb = s5.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📦 JSON Document Structure (telemetry_json)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE
    json_lines = [
        "{",
        '  "mission_source": "NASA Kepler / TESS",',
        '  "spectroscopy": {',
        '    "biosignature_status": "CANDIDATE_DETECTED",',
        '    "water_vapor_confidence": 0.88,',
        '    "methane_confidence": 0.65,',
        '    "spectroscopy_grade": "A+"',
        '  },',
        '  "astro_parameters": {',
        '    "eccentricity": 0.007,',
        '    "inclination_deg": 89.7',
        '  }',
        "}"
    ]
    for jl in json_lines:
        p = tf.add_paragraph()
        p.text = jl
        p.font.size = Pt(11)
        p.font.name = "Consolas"
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 6: THE CONFIDENCE DRIFT TRIGGER (THE INNOVATION)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    apply_background(s6)
    add_header(s6, "Core DBMS Innovation: The Confidence Drift Trigger")

    # Code breakdown box
    add_card(s6, Inches(0.9), Inches(1.9), Inches(11.5), Inches(4.7), C_CARD, C_GOLD)
    tb = s6.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚡ TRIGGER: trg_after_exoplanet_update (MySQL DML Trigger)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_GOLD

    trigger_lines = [
        "1. TRIGGER DEFINITION: CREATE TRIGGER trg_after_exoplanet_update AFTER UPDATE ON exoplanets FOR EACH ROW",
        "2. DETECT SCORE VARIANCE: IF (NEW.predicted_habitability <> OLD.predicted_habitability) THEN",
        "3. COMPUTE DELTA: SET delta = NEW.predicted_habitability - OLD.predicted_habitability;",
        "4. SIGNIFICANCE THRESHOLD CHECK: IF ABS(delta) >= 0.15 THEN -- 15% Confidence Shift Threshold",
        "       SET is_drift_alert = 1; -- Automatically flags alert badge on frontend",
        "       SET note_text = CONCAT('CONFIDENCE DRIFT: Delta ', ROUND(delta * 100, 1), '%');",
        "5. IMMUTABLE HISTORICAL LOGGING: INSERT INTO habitability_log (planet_id, old_score, new_score, delta, is_drift_alert...)",
        "6. AUDIT TRAIL LOGGING: INSERT INTO system_audit_trail (action, entity_type, entity_id, details...)"
    ]
    for tl in trigger_lines:
        p = tf.add_paragraph()
        p.text = tl
        p.font.size = Pt(12)
        p.font.name = "Consolas"
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(6)

    p_conc = tf.add_paragraph()
    p_conc.text = "🎯 DBMS Takeaway: The application code merely updates a row; the database itself computes variance, detects scientific drift, and writes audit history automatically."
    p_conc.font.size = Pt(12)
    p_conc.font.bold = True
    p_conc.font.color.rgb = C_CYAN
    p_conc.space_before = Pt(12)

    # =========================================================================
    # SLIDE 7: STORED PROCEDURES & DATABASE VIEWS
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    apply_background(s7)
    add_header(s7, "Server Execution: Stored Procedures & Views")

    # Left: Stored Procedure
    add_card(s7, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s7.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚙️ Stored Procedure: sp_GetCatalogOverviewStats"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    points = [
        "Compiled Server Execution: Runs directly inside MySQL's engine.",
        "Aggregates 6 key catalog metrics in a single network round-trip:",
        "  • Total Planets (4,048)",
        "  • Total Stars (3,010)",
        "  • Confirmed Habitable (57)",
        "  • Average ESI Score (0.370)",
        "  • Active Drift Alerts (10)",
        "  • Nearest Habitable Distance (4.24 LY)",
        "Benchmark: Executes in under 15ms across 4,000+ records!"
    ]
    for pt in points:
        p = tf.add_paragraph()
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(4)

    # Right: Views
    add_card(s7, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s7.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "👁️ Materialized Logic Views"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    views = [
        ("v_goldilocks_candidates", "Multi-table relational join (planets + stars) filtering worlds residing inside their host star's liquid water boundary."),
        ("v_star_systems_summary", "GROUP BY aggregation computing total worlds, habitable worlds, and average ESI per star system."),
        ("v_confidence_drift_alerts", "Pre-filtered view joining exoplanets and stars on habitability_log where is_drift_alert = 1."),
        ("v_top_earth_twins", "Top 25 terrestrial candidates ranked by composite Earth similarity formula.")
    ]
    for vname, vdesc in views:
        p = tf.add_paragraph()
        p.text = "• " + vname + ":"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_GOLD
        p.space_before = Pt(6)
        p2 = tf.add_paragraph()
        p2.text = "   " + vdesc
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_MUTED

    # =========================================================================
    # SLIDE 8: MACHINE LEARNING & ASTROBIOLOGY
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    apply_background(s8)
    add_header(s8, "Machine Learning: Random Forest Habitability Predictor")

    add_card(s8, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s8.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🌳 Random Forest Classifier (200 Trees)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_GREEN
    items = [
        "Why Random Forest? Astronomical boundaries are highly non-linear (planets too hot or too cold are non-habitable).",
        "Ensemble of 200 de-correlated decision trees voting on habitability probability (0.0 to 1.0).",
        "Extreme Class Imbalance Solution:",
        "  • Only 57 out of 4,048 planets (~1.4%) are habitable.",
        "  • Handled via class_weight='balanced' to heavily penalize false negatives.",
        "Model exported as model.pkl and cached in backend memory."
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = it
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(8)

    add_card(s8, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s8.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🧬 Feature Vector (10 Dimensions)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    feats = [
        "1. Earth Similarity Index (ESI score: 0.0 - 1.0)",
        "2. Habitable Zone Flag (1 inside Goldilocks, 0 outside)",
        "3. Planet Radius (R⊕ - Earth Radii)",
        "4. Planet Mass (M⊕ - Earth Masses)",
        "5. Equilibrium Temperature (Kelvin)",
        "6. Orbital Period (Days)",
        "7. Insolation Stellar Flux (relative to Earth)",
        "8. Host Star Temperature (Kelvin)",
        "9. Host Star Radius (R☉ - Solar Radii)",
        "10. Host Star Mass (M☉ - Solar Masses)"
    ]
    for f in feats:
        p = tf.add_paragraph()
        p.text = f
        p.font.size = Pt(11)
        p.font.name = "Consolas"
        p.font.color.rgb = C_MUTED
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 9: FRONTEND & ORBIT SIMULATOR (KEPLER'S LAWS)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    apply_background(s9)
    add_header(s9, "Frontend Engineering & Keplerian Orbit Simulator")

    add_card(s9, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s9.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🪐 Real-Time 2D Orbit Simulator"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_CYAN
    items = [
        "Pure HTML5 Canvas without heavy frameworks.",
        "Renders central star's corona flare colored by stellar spectral class (G-Type Yellow, M-Dwarf Red).",
        "Calculates Circumstellar Habitable Zone boundaries dynamically from stellar luminosity:",
        "    r_inner = sqrt(L / 1.1) AU",
        "    r_outer = sqrt(L / 0.53) AU",
        "Revolving planets obey Kepler's Third Law (T² ∝ a³): orbital angular velocity ω ∝ 1 / sqrt(a³)."
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = it
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(8)

    add_card(s9, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s9.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🎨 Manifestation of DBMS Concepts"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE
    items = [
        "Foreign Key Transparency: Table explicitly displays Host Star (Foreign Key) and FK ID # references.",
        "Confidence Drift Badges: Automated triggers visually pulse when a score shift ≥ 15% is detected.",
        "Deep Spectroscopy Modal: Surfacing the MySQL JSON document store (biosignatures and spectroscopy).",
        "Live NASA TAP Sync: Button hitting Caltech IPAC servers to insert newly confirmed exoplanets."
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = "• " + it
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(10)

    # =========================================================================
    # SLIDE 10: TEAM ROLES & LIVE DEMO CLICK PATH
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    apply_background(s10)
    add_header(s10, "Team Presentation Flow & Live Demo Script")

    add_card(s10, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD)
    tb = s10.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "👥 Team Speaking Division (4 Members)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE
    roles = [
        ("Member 1 (Intro):", "Problem background, data ingestion from NASA, static catalog limitations, and the Confidence Drift concept."),
        ("Member 2 (DBMS Core):", "3NF relational normalization, foreign key cascading constraints, stored procedures, and B-Tree indexes."),
        ("Member 3 (Triggers):", "Line-by-line explanation of trg_after_exoplanet_update, delta calculation, and audit trail tables."),
        ("Member 4 (ML & Demo):", "Random forest model, class imbalance strategy, live UI walkthrough, and NASA TAP synchronization.")
    ]
    for rtitle, rdesc in roles:
        p = tf.add_paragraph()
        p.text = rtitle
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_CYAN
        p.space_before = Pt(6)
        p2 = tf.add_paragraph()
        p2.text = rdesc
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_TEXT

    add_card(s10, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), C_CARD_ALT, C_GOLD)
    tb = s10.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.2), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🎯 Step-by-Step Live Demo Path"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_GOLD
    demo_steps = [
        "1. Open Mission Control: Show HUD metrics (4,048 worlds, 3,010 stars, 57 habitable worlds).",
        "2. Relational Search: Search 'TRAPPIST' — show foreign key links to star ID #2802.",
        "3. Orbit Simulator: Switch to TRAPPIST-1 — show the green habitable zone ring and revolving planets.",
        "4. TRIGGER THE NOVELTY: Edit Kepler-452 b, change mass from 5.0 to 500.0, hit Save.",
        "5. Verify: The ML model rescores it, the trigger detects the drop, and the ⚡ DRIFT badge appears!",
        "6. Drift Radar: Open the Drift Radar tab to inspect the historical audit trail generated by MySQL."
    ]
    for ds in demo_steps:
        p = tf.add_paragraph()
        p.text = ds
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 11: PROFESSOR VIVA Q&A DEFENSE
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    apply_background(s11)
    add_header(s11, "Anticipated Viva Defense Questions & Answers")

    viva = [
        ("Q: Why MySQL instead of MongoDB?", "A: Planets orbit stars in a strict 1-to-many relationship requiring ACID transactions and foreign key cascade integrity. However, to capture evolving telemetry, we implemented Polyglot Persistence inside MySQL 8.0, using JSON document columns for spectroscopy."),
        ("Q: What is the novelty of your project?", "A: Traditional catalogs are static. Our novelty is Confidence Drift Tracking: automated MySQL AFTER UPDATE triggers that compute variance (Δ = NEW - OLD) and flag significant shifts (≥ 15%) into an immutable audit log without external application logic."),
        ("Q: How do your triggers enforce referential integrity?", "A: fk_planet_star has ON DELETE CASCADE. If a host star is removed, all orbiting planets and their drift logs are purged automatically by InnoDB, preventing orphan records."),
        ("Q: Why Random Forest over Logistic Regression?", "A: Habitability boundaries are non-linear (extremes in either direction are non-habitable). Random Forest ensembles 200 decision trees and handles extreme class imbalance (1.4% habitable) via balanced class weights.")
    ]

    for idx, (q, a) in enumerate(viva):
        top_pos = Inches(1.85 + idx * 1.35)
        add_card(s11, Inches(0.9), top_pos, Inches(11.5), Inches(1.2), C_CARD)
        tb = s11.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.05), Inches(11.1), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = q
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = C_CYAN
        p2 = tf.add_paragraph()
        p2.text = a
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_TEXT
        p2.space_before = Pt(2)

    # =========================================================================
    # SLIDE 12: CONCLUSION & SUMMARY
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    apply_background(s12)
    add_card(s12, Inches(1.5), Inches(1.5), Inches(10.333), Inches(4.5), C_CARD, C_GREEN)

    tb = s12.shapes.add_textbox(Inches(2.0), Inches(2.0), Inches(9.333), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "✨ Thank You! Questions & Discussion"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = C_TEXT

    p = tf.add_paragraph()
    p.text = "Exoplanet Habitability Catalog — A Full-Stack DBMS Capstone Achievement"
    p.font.size = Pt(17)
    p.font.color.rgb = C_GREEN
    p.space_before = Pt(12)

    items = [
        "3NF Relational Model: 3,010 real star systems and 4,048 exoplanets.",
        "Automated MySQL Triggers: Real-time Confidence Drift engine flagging shifts ≥ 15%.",
        "Polyglot JSON Documents: Deep spectroscopy and biosignature storage.",
        "Interactive Keplerian Orbit Simulator: Circumstellar liquid-water zone dynamics."
    ]
    for it in items:
        p = tf.add_paragraph()
        p.text = "• " + it
        p.font.size = Pt(13)
        p.font.color.rgb = C_MUTED
        p.space_before = Pt(8)

    # Output path
    out_path = os.path.join(os.path.dirname(__file__), 'Exoplanet_Habitability_Presentation.pptx')
    prs.save(out_path)
    print(f"Presentation saved successfully to: {out_path}")

if __name__ == '__main__':
    create_deck()
