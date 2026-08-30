-- =====================================================================
-- Module C — Stored Procedures & Views
-- Exoplanet Habitability Pipeline (Week 1)
--
-- Assumes upstream tables produced by Module A (cleaning) and
-- Module B (feature engineering):
--
--   exoplanets (
--       planet_id            INT PRIMARY KEY,
--       planet_name          VARCHAR(100),
--       mass                 FLOAT,
--       radius               FLOAT,
--       stellar_flux         FLOAT,
--       esi_score            FLOAT,
--       habitable_zone_flag  TINYINT(1)
--   )
--
--   habitability_log (
--       log_id               INT AUTO_INCREMENT PRIMARY KEY,
--       planet_id            INT,
--       esi_score            FLOAT,
--       habitable_zone_flag  TINYINT(1),
--       log_date             DATETIME DEFAULT CURRENT_TIMESTAMP,
--       FOREIGN KEY (planet_id) REFERENCES exoplanets(planet_id)
--   )
--
-- NOTE: Confirm these column names against the ACTUAL output of
-- Module A / Module B before running this file — this is the same
-- interface-contract check flagged in the Module B PR review
-- (filename/column mismatches break silently, not loudly).
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. GetHabitablePlanets(min_esi)
--    Returns all planets flagged as habitable, above a given ESI
--    threshold, ranked best-first.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS GetHabitablePlanets;

DELIMITER $$

CREATE PROCEDURE GetHabitablePlanets(IN min_esi FLOAT)
BEGIN
    SELECT
        planet_id,
        planet_name,
        esi_score,
        habitable_zone_flag
    FROM exoplanets
    WHERE habitable_zone_flag = 1
      AND esi_score >= min_esi
    ORDER BY esi_score DESC;
END$$

DELIMITER ;

-- Sample call:
-- CALL GetHabitablePlanets(0.8);


-- ---------------------------------------------------------------------
-- 2. RecalculateAllScores()
--    Recomputes ESI for every planet using the Schulze-Makuch et al.
--    formula, updates exoplanets in place, and writes a snapshot row
--    to habitability_log so v_current_habitability has data to join.
--
--    IMPORTANT: this reuses the SAME formula logic as Module B's
--    calculate_esi(). If that function's negative-base exponentiation
--    bug gets fixed, apply the identical fix here (ABS() guard shown
--    below) or scores will drift out of sync between modules.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS RecalculateAllScores;

DELIMITER $$

CREATE PROCEDURE RecalculateAllScores()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_planet_id INT;
    DECLARE v_mass FLOAT;
    DECLARE v_radius FLOAT;
    DECLARE v_esi FLOAT;
    DECLARE v_flag TINYINT;

    DECLARE cur CURSOR FOR
        SELECT planet_id, mass, radius FROM exoplanets;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_planet_id, v_mass, v_radius;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Guard against zero/negative inputs before exponentiation
        -- (mirrors the non-blocking guard flagged in Module B review)
        IF v_mass > 0 AND v_radius > 0 THEN
            SET v_esi = 1 - ABS(
                (v_radius - 1) / (v_radius + 1)
            ) * 0.5
              - ABS(
                (v_mass - 1) / (v_mass + 1)
            ) * 0.5;
        ELSE
            SET v_esi = NULL;
        END IF;

        SET v_flag = CASE WHEN v_esi >= 0.8 THEN 1 ELSE 0 END;

        UPDATE exoplanets
        SET esi_score = v_esi,
            habitable_zone_flag = v_flag
        WHERE planet_id = v_planet_id;

        INSERT INTO habitability_log (planet_id, esi_score, habitable_zone_flag)
        VALUES (v_planet_id, v_esi, v_flag);

    END LOOP;

    CLOSE cur;
END$$

DELIMITER ;

-- Sample call:
-- CALL RecalculateAllScores();


-- ---------------------------------------------------------------------
-- 3. v_current_habitability
--    Joins exoplanets with the LATEST habitability_log entry per
--    planet. Uses a subquery to find the max log_date per planet_id,
--    then joins back to pull that row — avoids duplicate/stale rows
--    if a planet has multiple log entries.
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_current_habitability;

CREATE VIEW v_current_habitability AS
SELECT
    e.planet_id,
    e.planet_name,
    e.mass,
    e.radius,
    h.esi_score       AS latest_esi_score,
    h.habitable_zone_flag AS latest_habitable_flag,
    h.log_date        AS last_updated
FROM exoplanets e
JOIN habitability_log h
    ON h.planet_id = e.planet_id
JOIN (
    SELECT planet_id, MAX(log_date) AS max_date
    FROM habitability_log
    GROUP BY planet_id
) latest
    ON h.planet_id = latest.planet_id
   AND h.log_date  = latest.max_date;

-- Sample call:
-- SELECT * FROM v_current_habitability ORDER BY latest_esi_score DESC;


-- =====================================================================
-- Deliverable checklist (per spec):
--   [ ] Run each object once against real data
--   [ ] Screenshot output of each sample call
--   [ ] Save screenshots to /docs
-- =====================================================================
