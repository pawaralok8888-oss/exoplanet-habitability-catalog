-- Run once against databases created before stellar_flux was added.
ALTER TABLE exoplanets
    ADD COLUMN stellar_flux DECIMAL(12,6) NULL AFTER orbital_distance;
