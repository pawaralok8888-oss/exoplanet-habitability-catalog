-- View: current habitability joined with latest log entry
CREATE OR REPLACE VIEW v_current_habitability AS
SELECT e.*, hl.prediction_timestamp AS last_prediction_time
FROM exoplanets e
JOIN habitability_log hl ON e.planet_id = hl.planet_id
WHERE hl.log_id = (
    SELECT MAX(log_id) FROM habitability_log WHERE planet_id = e.planet_id
);

-- Stored procedure: get all habitable planets
DELIMITER $$
DROP PROCEDURE IF EXISTS GetHabitablePlanets$$
CREATE PROCEDURE GetHabitablePlanets()
BEGIN
    SELECT * FROM exoplanets WHERE predicted_habitability >= 0.5;
END$$
DELIMITER ;

-- Stored procedure: get drift history for one planet (powers the novelty feature)
DELIMITER $$
DROP PROCEDURE IF EXISTS GetDriftHistory$$
CREATE PROCEDURE GetDriftHistory(IN p_id INT)
BEGIN
    SELECT predicted_habitability, prediction_timestamp
    FROM habitability_log
    WHERE planet_id = p_id
    ORDER BY prediction_timestamp ASC;
END$$
DELIMITER ;
