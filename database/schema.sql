-- stars table
CREATE TABLE IF NOT EXISTS stars (
    star_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    temperature DECIMAL(10,2),
    radius DECIMAL(10,4),
    mass DECIMAL(10,4),
    distance_from_earth DECIMAL(12,4)
);

-- exoplanets table
CREATE TABLE IF NOT EXISTS exoplanets (
    planet_id INT AUTO_INCREMENT PRIMARY KEY,
    star_id INT,
    name VARCHAR(100) NOT NULL,
    radius DECIMAL(10,4),
    mass DECIMAL(10,4),
    orbital_period DECIMAL(12,4),
    orbital_distance DECIMAL(12,6),
    equilibrium_temp DECIMAL(10,2),
    esi_score DECIMAL(5,4),
    habitable_zone_flag TINYINT(1),
    predicted_habitability DECIMAL(5,4),
    discovery_year INT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (star_id) REFERENCES stars(star_id) ON DELETE SET NULL
);
