-- Preserve physical properties, host-star HZ boundaries, and provenance
-- needed by the scientist workspace. Run once on an existing database.
ALTER TABLE stars
    ADD COLUMN stellar_type VARCHAR(64) NULL,
    ADD COLUMN age DECIMAL(10,4) NULL,
    ADD COLUMN luminosity DECIMAL(14,8) NULL,
    ADD COLUMN hz_conservative_inner_au DECIMAL(14,8) NULL,
    ADD COLUMN hz_conservative_outer_au DECIMAL(14,8) NULL;

ALTER TABLE exoplanets
    ADD COLUMN density DECIMAL(14,8) NULL,
    ADD COLUMN gravity DECIMAL(14,8) NULL,
    ADD COLUMN escape_velocity DECIMAL(14,8) NULL,
    ADD COLUMN habitable_zone_optimistic_flag TINYINT(1) NULL,
    ADD COLUMN detection_method VARCHAR(100) NULL,
    ADD COLUMN planet_type VARCHAR(64) NULL,
    ADD COLUMN data_source VARCHAR(100) NULL;
