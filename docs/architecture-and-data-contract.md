# Architecture and data contract

## Request path

`frontend → Flask routes → services → repositories → MySQL`

- Route modules translate HTTP requests and responses.
- `backend/services.py` validates input and coordinates prediction plus persistence.
- `backend/repositories.py` contains application SQL.
- `backend/db.py` owns the MySQL connection pool, transaction boundary, and cursor cleanup.
- `backend/predictor.py` loads the saved scikit-learn pipeline.

## Canonical database names

The running app uses `stars.name`, `exoplanets.name`, and these prediction-history fields:
`habitability_log.predicted_habitability` and `habitability_log.prediction_timestamp`.
`exoplanets.stellar_flux` stores incident stellar flux in the same units as the model's
`P_FLUX` training feature. The Python field `planet_name` is not used by this schema.

For a new database, run these files in order:

1. `database/schema.sql`
2. `database/habitability_log.sql`
3. `database/procedures.sql`

For a database created before `stellar_flux` was added, run
`database/migrations/001_add_stellar_flux.sql` once before using the updated API.

## Model input contract

`model/feature_contract.py` is the single source for the model feature order:
`esi_score`, `habitable_zone_flag`, radius, mass, equilibrium temperature, orbital
period, stellar flux, and host-star temperature/radius/mass. Planet values use the
same units as the PHL training CSV. `stellar_flux` maps to `P_FLUX`; orbital distance
is a separate field and must not be used as a substitute. Missing values are left
missing at the API boundary and filled by the median imputer inside the saved model
pipeline, using medians learned from its training split.

When retraining, run `python model/train_model.py` from this project directory. This
regenerates `model.pkl`, which stores both the imputer and classifier.
