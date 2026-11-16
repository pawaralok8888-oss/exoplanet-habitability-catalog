-- Upgrade an existing database to retain score changes, changed inputs, source,
-- and model version. Run once after migrations 001 and 002.
ALTER TABLE exoplanets
    ADD COLUMN model_version VARCHAR(32) NULL;

ALTER TABLE habitability_log
    ADD COLUMN old_score DECIMAL(5,4) NULL,
    ADD COLUMN new_score DECIMAL(5,4) NULL,
    ADD COLUMN score_delta DECIMAL(5,4) NULL,
    ADD COLUMN changed_fields JSON NULL,
    ADD COLUMN data_source VARCHAR(100) NULL,
    ADD COLUMN model_version VARCHAR(32) NULL,
    ADD COLUMN changed_at DATETIME NULL;

-- Preserve old history for the existing timeline; historical changed fields
-- and model versions cannot be reconstructed from the old log.
UPDATE habitability_log
SET new_score = predicted_habitability,
    changed_at = prediction_timestamp;

DELIMITER $$
DROP TRIGGER IF EXISTS after_exoplanet_insert$$
CREATE TRIGGER after_exoplanet_insert
AFTER INSERT ON exoplanets
FOR EACH ROW
BEGIN
    INSERT INTO habitability_log (
        planet_id, old_score, new_score, score_delta, changed_fields,
        data_source, model_version, changed_at, predicted_habitability, prediction_timestamp
    ) VALUES (
        NEW.planet_id, NULL, NEW.predicted_habitability, NULL, JSON_ARRAY(),
        NEW.data_source, NEW.model_version, NOW(), NEW.predicted_habitability, NOW()
    );
END$$

DROP TRIGGER IF EXISTS after_exoplanet_update$$
CREATE TRIGGER after_exoplanet_update
AFTER UPDATE ON exoplanets
FOR EACH ROW
BEGIN
    DECLARE changed JSON;
    SET changed = JSON_ARRAY();

    IF NOT (NEW.name <=> OLD.name) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'name', 'old', OLD.name, 'new', NEW.name));
    END IF;
    IF NOT (NEW.star_id <=> OLD.star_id) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'star_id', 'old', OLD.star_id, 'new', NEW.star_id));
    END IF;
    IF NOT (NEW.radius <=> OLD.radius) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'radius', 'old', OLD.radius, 'new', NEW.radius));
    END IF;
    IF NOT (NEW.mass <=> OLD.mass) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'mass', 'old', OLD.mass, 'new', NEW.mass));
    END IF;
    IF NOT (NEW.orbital_period <=> OLD.orbital_period) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'orbital_period', 'old', OLD.orbital_period, 'new', NEW.orbital_period));
    END IF;
    IF NOT (NEW.orbital_distance <=> OLD.orbital_distance) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'orbital_distance', 'old', OLD.orbital_distance, 'new', NEW.orbital_distance));
    END IF;
    IF NOT (NEW.stellar_flux <=> OLD.stellar_flux) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'stellar_flux', 'old', OLD.stellar_flux, 'new', NEW.stellar_flux));
    END IF;
    IF NOT (NEW.equilibrium_temp <=> OLD.equilibrium_temp) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'equilibrium_temp', 'old', OLD.equilibrium_temp, 'new', NEW.equilibrium_temp));
    END IF;
    IF NOT (NEW.esi_score <=> OLD.esi_score) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'esi_score', 'old', OLD.esi_score, 'new', NEW.esi_score));
    END IF;
    IF NOT (NEW.density <=> OLD.density) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'density', 'old', OLD.density, 'new', NEW.density));
    END IF;
    IF NOT (NEW.gravity <=> OLD.gravity) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'gravity', 'old', OLD.gravity, 'new', NEW.gravity));
    END IF;
    IF NOT (NEW.escape_velocity <=> OLD.escape_velocity) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'escape_velocity', 'old', OLD.escape_velocity, 'new', NEW.escape_velocity));
    END IF;
    IF NOT (NEW.habitable_zone_flag <=> OLD.habitable_zone_flag) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'habitable_zone_flag', 'old', OLD.habitable_zone_flag, 'new', NEW.habitable_zone_flag));
    END IF;
    IF NOT (NEW.habitable_zone_optimistic_flag <=> OLD.habitable_zone_optimistic_flag) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'habitable_zone_optimistic_flag', 'old', OLD.habitable_zone_optimistic_flag, 'new', NEW.habitable_zone_optimistic_flag));
    END IF;
    IF NOT (NEW.discovery_year <=> OLD.discovery_year) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'discovery_year', 'old', OLD.discovery_year, 'new', NEW.discovery_year));
    END IF;
    IF NOT (NEW.detection_method <=> OLD.detection_method) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'detection_method', 'old', OLD.detection_method, 'new', NEW.detection_method));
    END IF;
    IF NOT (NEW.planet_type <=> OLD.planet_type) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'planet_type', 'old', OLD.planet_type, 'new', NEW.planet_type));
    END IF;
    IF NOT (NEW.data_source <=> OLD.data_source) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'data_source', 'old', OLD.data_source, 'new', NEW.data_source));
    END IF;
    IF NOT (NEW.model_version <=> OLD.model_version) THEN
        SET changed = JSON_ARRAY_APPEND(changed, '$', JSON_OBJECT('field', 'model_version', 'old', OLD.model_version, 'new', NEW.model_version));
    END IF;

    IF NOT (NEW.predicted_habitability <=> OLD.predicted_habitability) OR JSON_LENGTH(changed) > 0 THEN
        INSERT INTO habitability_log (
            planet_id, old_score, new_score, score_delta, changed_fields,
            data_source, model_version, changed_at, predicted_habitability, prediction_timestamp
        ) VALUES (
            NEW.planet_id, OLD.predicted_habitability, NEW.predicted_habitability,
            CASE WHEN OLD.predicted_habitability IS NOT NULL AND NEW.predicted_habitability IS NOT NULL
                 THEN ABS(NEW.predicted_habitability - OLD.predicted_habitability) ELSE NULL END,
            changed, NEW.data_source, NEW.model_version, NOW(),
            NEW.predicted_habitability, NOW()
        );
    END IF;
END$$
DELIMITER ;
