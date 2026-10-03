-- habitability_log table (history of predictions, powers Confidence Drift)
CREATE TABLE IF NOT EXISTS habitability_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    planet_id INT NOT NULL,
    predicted_habitability DECIMAL(5,4),
    prediction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planet_id) REFERENCES exoplanets(planet_id) ON DELETE CASCADE
);

-- Trigger: log on insert
DELIMITER $$
DROP TRIGGER IF EXISTS after_exoplanet_insert$$
CREATE TRIGGER after_exoplanet_insert
AFTER INSERT ON exoplanets
FOR EACH ROW
BEGIN
    INSERT INTO habitability_log (planet_id, predicted_habitability, prediction_timestamp)
    VALUES (NEW.planet_id, NEW.predicted_habitability, NOW());
END$$
DELIMITER ;

-- Trigger: log on update (only when score actually changes)
DELIMITER $$
DROP TRIGGER IF EXISTS after_exoplanet_update$$
CREATE TRIGGER after_exoplanet_update
AFTER UPDATE ON exoplanets
FOR EACH ROW
BEGIN
    IF NEW.predicted_habitability <> OLD.predicted_habitability OR (OLD.predicted_habitability IS NULL AND NEW.predicted_habitability IS NOT NULL) THEN
        INSERT INTO habitability_log (planet_id, predicted_habitability, prediction_timestamp)
        VALUES (NEW.planet_id, NEW.predicted_habitability, NOW());
    END IF;
END$$
DELIMITER ;
