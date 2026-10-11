-- ==============================================================================
-- EXOPLANET HABITABILITY CATALOG — MEGA DBMS ARCHITECTURE (MySQL 8.0+)
-- Features: 3NF Relational Normalization, Polyglot JSON Documents, Automated Audit
-- Triggers, Stored Procedures, Aggregated Views, and B-Tree Performance Indexes.
-- ==============================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS system_audit_trail;
DROP TABLE IF EXISTS research_bookmarks;
DROP TABLE IF EXISTS habitability_log;
DROP TABLE IF EXISTS exoplanets;
DROP TABLE IF EXISTS stars;
DROP TABLE IF EXISTS discovery_methods;

DROP VIEW IF EXISTS v_goldilocks_candidates;
DROP VIEW IF EXISTS v_star_systems_summary;
DROP VIEW IF EXISTS v_confidence_drift_alerts;
DROP VIEW IF EXISTS v_top_earth_twins;
DROP VIEW IF EXISTS v_discovery_method_stats;
DROP VIEW IF EXISTS v_current_habitability;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------------------------
-- 1. DISCOVERY METHODS (Lookup / Normalization Table)
-- ------------------------------------------------------------------------------
CREATE TABLE discovery_methods (
    method_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    technique_type VARCHAR(50) DEFAULT 'Indirect'
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 2. STARS (Host Star Systems)
-- ------------------------------------------------------------------------------
CREATE TABLE stars (
    star_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    spectral_type VARCHAR(30) DEFAULT 'Unknown',
    temperature DECIMAL(10,2),           -- Kelvin
    radius DECIMAL(10,4),                -- Solar Radii (R☉)
    mass DECIMAL(10,4),                  -- Solar Masses (M☉)
    luminosity DECIMAL(14,6),            -- Solar Luminosity (L☉)
    distance_from_earth DECIMAL(12,4),   -- Light-Years
    constellation VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 3. EXOPLANETS (Core Planetary Entities + Hybrid JSON Telemetry)
-- ------------------------------------------------------------------------------
CREATE TABLE exoplanets (
    planet_id INT AUTO_INCREMENT PRIMARY KEY,
    star_id INT NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,
    planet_type VARCHAR(50) DEFAULT 'Terran',  -- Terran, Superterran, Jovian, Neptunian
    radius DECIMAL(10,4),                     -- Earth Radii (R⊕)
    mass DECIMAL(10,4),                       -- Earth Masses (M⊕)
    orbital_period DECIMAL(14,4),             -- Days
    orbital_distance DECIMAL(12,6),           -- Semi-major axis in AU
    equilibrium_temp DECIMAL(10,2),           -- Kelvin
    stellar_flux DECIMAL(12,4),               -- Insolation relative to Earth
    esi_score DECIMAL(5,4),                   -- Earth Similarity Index (0.0 to 1.0)
    habitable_zone_flag TINYINT(1) DEFAULT 0, -- 1 if inside Goldilocks zone
    predicted_habitability DECIMAL(5,4),      -- ML Random Forest Output (0.0 to 1.0)
    discovery_year INT,
    discovery_method_id INT,
    telemetry_json JSON,                      -- Hybrid NoSQL: Deep telemetry & spectra
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_planet_star FOREIGN KEY (star_id) REFERENCES stars(star_id) ON DELETE CASCADE,
    CONSTRAINT fk_planet_method FOREIGN KEY (discovery_method_id) REFERENCES discovery_methods(method_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 4. HABITABILITY LOG (Audit Trail & Confidence Drift Engine)
-- ------------------------------------------------------------------------------
CREATE TABLE habitability_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    planet_id INT NOT NULL,
    old_score DECIMAL(5,4),
    new_score DECIMAL(5,4) NOT NULL,
    score_delta DECIMAL(6,4) DEFAULT 0.0000,
    change_type VARCHAR(40) DEFAULT 'OBSERVATION_UPDATE',
    is_drift_alert TINYINT(1) DEFAULT 0,      -- Flagged if score changed >= 0.15
    notes VARCHAR(255),
    prediction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_log_planet FOREIGN KEY (planet_id) REFERENCES exoplanets(planet_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 5. RESEARCH BOOKMARKS (Active Investigation Pins)
-- ------------------------------------------------------------------------------
CREATE TABLE research_bookmarks (
    bookmark_id INT AUTO_INCREMENT PRIMARY KEY,
    planet_id INT NOT NULL,
    researcher_name VARCHAR(100) DEFAULT 'Lead Mission Specialist',
    notes TEXT,
    priority VARCHAR(20) DEFAULT 'HIGH',      -- LOW, MEDIUM, HIGH, CRITICAL
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bookmark_planet FOREIGN KEY (planet_id) REFERENCES exoplanets(planet_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 6. SYSTEM AUDIT TRAIL (General DML Operation Logging)
-- ------------------------------------------------------------------------------
CREATE TABLE system_audit_trail (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(50) NOT NULL,              -- INSERT, UPDATE, DELETE, NASA_TAP_SYNC
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    details TEXT,
    performed_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- B-TREE PERFORMANCE INDEXES
-- ------------------------------------------------------------------------------
CREATE INDEX idx_exoplanet_scores ON exoplanets(predicted_habitability, esi_score);
CREATE INDEX idx_exoplanet_star ON exoplanets(star_id);
CREATE INDEX idx_exoplanet_type ON exoplanets(planet_type);
CREATE INDEX idx_stars_distance ON stars(distance_from_earth);
CREATE INDEX idx_log_planet_time ON habitability_log(planet_id, prediction_timestamp);

-- ==============================================================================
-- DATABASE TRIGGERS
-- ==============================================================================

DELIMITER $$

-- Trigger 1: Automatic Audit on Planet Insertion
DROP TRIGGER IF EXISTS trg_after_exoplanet_insert$$
CREATE TRIGGER trg_after_exoplanet_insert
AFTER INSERT ON exoplanets
FOR EACH ROW
BEGIN
    INSERT INTO habitability_log (
        planet_id, old_score, new_score, score_delta, change_type, is_drift_alert, notes, prediction_timestamp
    )
    VALUES (
        NEW.planet_id,
        NULL,
        COALESCE(NEW.predicted_habitability, 0.0),
        0.0000,
        'INITIAL_OBSERVATION',
        0,
        CONCAT('Initial discovery catalogued for ', NEW.name),
        NOW()
    );

    INSERT INTO system_audit_trail (action, entity_type, entity_id, details)
    VALUES ('INSERT', 'EXOPLANET', NEW.planet_id, CONCAT('New world catalogued: ', NEW.name));
END$$

-- Trigger 2: Confidence Drift Engine on Planet Update
DROP TRIGGER IF EXISTS trg_after_exoplanet_update$$
CREATE TRIGGER trg_after_exoplanet_update
AFTER UPDATE ON exoplanets
FOR EACH ROW
BEGIN
    DECLARE delta DECIMAL(6,4);
    DECLARE alert TINYINT(1) DEFAULT 0;
    DECLARE note_text VARCHAR(255);

    -- Detect score modification or first-time scoring
    IF (OLD.predicted_habitability IS NULL AND NEW.predicted_habitability IS NOT NULL) OR 
       (NEW.predicted_habitability <> OLD.predicted_habitability) THEN
        
        SET delta = COALESCE(NEW.predicted_habitability, 0.0) - COALESCE(OLD.predicted_habitability, 0.0);
        
        -- Flag as Significant Drift Alert if delta magnitude is >= 0.15 (15%)
        IF ABS(delta) >= 0.15 THEN
            SET alert = 1;
            IF delta > 0 THEN
                SET note_text = CONCAT('CONFIDENCE DRIFT: Habitability surged by +', ROUND(delta * 100, 1), '%');
            ELSE
                SET note_text = CONCAT('CONFIDENCE DRIFT: Habitability dropped by ', ROUND(delta * 100, 1), '%');
            END IF;
        ELSE
            SET alert = 0;
            SET note_text = CONCAT('Routine telemetry refinement (delta: ', ROUND(delta * 100, 2), '%)');
        END IF;

        INSERT INTO habitability_log (
            planet_id, old_score, new_score, score_delta, change_type, is_drift_alert, notes, prediction_timestamp
        )
        VALUES (
            NEW.planet_id,
            OLD.predicted_habitability,
            NEW.predicted_habitability,
            delta,
            'REFINEMENT_UPDATE',
            alert,
            note_text,
            NOW()
        );
    END IF;

    INSERT INTO system_audit_trail (action, entity_type, entity_id, details)
    VALUES ('UPDATE', 'EXOPLANET', NEW.planet_id, CONCAT('Telemetry updated for ', NEW.name));
END$$

-- Trigger 3: Astrophysical Physics Validation
DROP TRIGGER IF EXISTS trg_validate_planetary_physics$$
CREATE TRIGGER trg_validate_planetary_physics
BEFORE INSERT ON exoplanets
FOR EACH ROW
BEGIN
    IF NEW.radius IS NOT NULL AND NEW.radius <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Astrophysical validation failed: Planet radius must be strictly positive.';
    END IF;
    IF NEW.mass IS NOT NULL AND NEW.mass <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Astrophysical validation failed: Planet mass must be strictly positive.';
    END IF;
END$$

-- Trigger 4: Audit Deletion
DROP TRIGGER IF EXISTS trg_after_exoplanet_delete$$
CREATE TRIGGER trg_after_exoplanet_delete
AFTER DELETE ON exoplanets
FOR EACH ROW
BEGIN
    INSERT INTO system_audit_trail (action, entity_type, entity_id, details)
    VALUES ('DELETE', 'EXOPLANET', OLD.planet_id, CONCAT('Planet decommissioned from catalog: ', OLD.name));
END$$

DELIMITER ;

-- ==============================================================================
-- DATABASE VIEWS
-- ==============================================================================

-- View 1: Goldilocks Zone Candidates (Liquid Water Suitable)
CREATE OR REPLACE VIEW v_goldilocks_candidates AS
SELECT 
    e.planet_id,
    e.name AS planet_name,
    s.name AS star_name,
    s.spectral_type,
    s.distance_from_earth,
    e.planet_type,
    e.radius,
    e.mass,
    e.equilibrium_temp,
    e.esi_score,
    e.predicted_habitability,
    e.discovery_year,
    dm.name AS discovery_method
FROM exoplanets e
JOIN stars s ON e.star_id = s.star_id
LEFT JOIN discovery_methods dm ON e.discovery_method_id = dm.method_id
WHERE e.predicted_habitability >= 0.45 OR e.habitable_zone_flag = 1
ORDER BY e.predicted_habitability DESC;

-- View 2: Star Systems Census Summary
CREATE OR REPLACE VIEW v_star_systems_summary AS
SELECT 
    s.star_id,
    s.name AS star_name,
    s.spectral_type,
    s.temperature AS star_temp,
    s.distance_from_earth,
    s.constellation,
    COUNT(e.planet_id) AS total_planets,
    SUM(CASE WHEN e.predicted_habitability >= 0.5 THEN 1 ELSE 0 END) AS habitable_planets,
    MAX(e.predicted_habitability) AS highest_system_habitability,
    AVG(e.esi_score) AS avg_system_esi
FROM stars s
LEFT JOIN exoplanets e ON s.star_id = e.star_id
GROUP BY s.star_id, s.name, s.spectral_type, s.temperature, s.distance_from_earth, s.constellation
ORDER BY total_planets DESC;

-- View 3: Active Confidence Drift Alerts
CREATE OR REPLACE VIEW v_confidence_drift_alerts AS
SELECT 
    hl.log_id,
    hl.planet_id,
    e.name AS planet_name,
    s.name AS star_name,
    hl.old_score,
    hl.new_score,
    hl.score_delta,
    hl.notes,
    hl.prediction_timestamp
FROM habitability_log hl
JOIN exoplanets e ON hl.planet_id = e.planet_id
JOIN stars s ON e.star_id = s.star_id
WHERE hl.is_drift_alert = 1
ORDER BY hl.prediction_timestamp DESC;

-- View 4: Top 25 Earth Twins
CREATE OR REPLACE VIEW v_top_earth_twins AS
SELECT 
    e.planet_id,
    e.name,
    s.name AS host_star,
    s.distance_from_earth AS distance_ly,
    e.radius,
    e.mass,
    e.equilibrium_temp,
    e.esi_score,
    e.predicted_habitability
FROM exoplanets e
JOIN stars s ON e.star_id = s.star_id
ORDER BY (COALESCE(e.predicted_habitability, 0) * 0.6 + COALESCE(e.esi_score, 0) * 0.4) DESC
LIMIT 25;

-- View 5: Backward-Compatible Current Habitability
CREATE OR REPLACE VIEW v_current_habitability AS
SELECT 
    e.*, 
    hl.prediction_timestamp AS last_prediction_time,
    hl.score_delta AS latest_drift_delta
FROM exoplanets e
LEFT JOIN habitability_log hl ON e.planet_id = hl.planet_id
WHERE hl.log_id = (
    SELECT MAX(sub_hl.log_id) FROM habitability_log sub_hl WHERE sub_hl.planet_id = e.planet_id
) OR hl.log_id IS NULL;

-- ==============================================================================
-- STORED PROCEDURES
-- ==============================================================================

DELIMITER $$

-- Procedure 1: Filter habitable candidates with multiple criteria
DROP PROCEDURE IF EXISTS sp_GetHabitableCandidates$$
CREATE PROCEDURE sp_GetHabitableCandidates(
    IN p_min_esi DECIMAL(5,4),
    IN p_min_prob DECIMAL(5,4),
    IN p_max_dist DECIMAL(12,4)
)
BEGIN
    SELECT 
        e.planet_id,
        e.name AS planet_name,
        s.name AS star_name,
        s.spectral_type,
        s.distance_from_earth,
        e.radius,
        e.mass,
        e.equilibrium_temp,
        e.esi_score,
        e.predicted_habitability
    FROM exoplanets e
    JOIN stars s ON e.star_id = s.star_id
    WHERE (e.esi_score >= p_min_esi OR p_min_esi IS NULL)
      AND (e.predicted_habitability >= p_min_prob OR p_min_prob IS NULL)
      AND (s.distance_from_earth <= p_max_dist OR p_max_dist IS NULL)
    ORDER BY e.predicted_habitability DESC;
END$$

-- Procedure 2: Complete Star System Hierarchy
DROP PROCEDURE IF EXISTS sp_GetStarSystemHierarchy$$
CREATE PROCEDURE sp_GetStarSystemHierarchy(IN p_star_id INT)
BEGIN
    -- Return star metadata
    SELECT * FROM stars WHERE star_id = p_star_id;

    -- Return orbiting planetary entourage
    SELECT 
        planet_id, name, planet_type, radius, mass, 
        orbital_period, orbital_distance, equilibrium_temp, 
        esi_score, habitable_zone_flag, predicted_habitability
    FROM exoplanets
    WHERE star_id = p_star_id
    ORDER BY orbital_distance ASC, orbital_period ASC;
END$$

-- Procedure 3: Drift History for specific planet
DROP PROCEDURE IF EXISTS sp_GetDriftHistory$$
CREATE PROCEDURE sp_GetDriftHistory(IN p_planet_id INT)
BEGIN
    SELECT 
        log_id,
        old_score,
        new_score,
        score_delta,
        change_type,
        is_drift_alert,
        notes,
        prediction_timestamp
    FROM habitability_log
    WHERE planet_id = p_planet_id
    ORDER BY prediction_timestamp ASC;
END$$

-- Procedure 4: Catalog Overview Aggregate Statistics
DROP PROCEDURE IF EXISTS sp_GetCatalogOverviewStats$$
CREATE PROCEDURE sp_GetCatalogOverviewStats()
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM exoplanets) AS total_planets,
        (SELECT COUNT(*) FROM stars) AS total_stars,
        (SELECT COUNT(*) FROM exoplanets WHERE predicted_habitability >= 0.5) AS habitable_candidates,
        (SELECT ROUND(AVG(esi_score), 3) FROM exoplanets WHERE esi_score IS NOT NULL) AS avg_esi_score,
        (SELECT COUNT(*) FROM habitability_log WHERE is_drift_alert = 1) AS total_drift_alerts,
        (SELECT MIN(s.distance_from_earth) FROM exoplanets e JOIN stars s ON e.star_id = s.star_id WHERE e.predicted_habitability >= 0.5) AS nearest_habitable_dist_ly;
END$$

-- Backward-Compatible Procedure: GetHabitablePlanets
DROP PROCEDURE IF EXISTS GetHabitablePlanets$$
CREATE PROCEDURE GetHabitablePlanets()
BEGIN
    SELECT * FROM exoplanets WHERE predicted_habitability >= 0.5 ORDER BY predicted_habitability DESC;
END$$

-- Backward-Compatible Procedure: GetDriftHistory
DROP PROCEDURE IF EXISTS GetDriftHistory$$
CREATE PROCEDURE GetDriftHistory(IN p_id INT)
BEGIN
    SELECT predicted_habitability, prediction_timestamp
    FROM habitability_log
    WHERE planet_id = p_id
    ORDER BY prediction_timestamp ASC;
END$$

DELIMITER ;
