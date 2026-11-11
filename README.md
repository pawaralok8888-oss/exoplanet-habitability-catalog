# Exoplanet Habitability Catalog

Flask and MySQL application with a static browser dashboard and a scikit-learn
habitability classifier.

## Setup overview

1. Create a MySQL database (default name: `exoplanets_db`).
2. Run the SQL files in order: `database/schema.sql`,
   `database/habitability_log.sql`, then `database/procedures.sql`.
3. If upgrading an older database, run `database/migrations/001_add_stellar_flux.sql`
   and `database/migrations/002_add_scientist_fields.sql` once before starting the updated API.
4. Install dependencies from `requirements.txt` and configure `DB_HOST`, `DB_USER`,
   `DB_PASSWORD`, `DB_NAME`, and optionally `DB_POOL_SIZE`.
5. Rebuild catalog features with `python features.py`, then train the saved
   preprocessing and prediction pipeline with `python model/train_model.py`.
6. Load or refresh the catalog with `python database/load_data.py`. Repeated runs
   refresh matching planet names instead of adding a second copy.
7. Start the API with `python backend/app.py`.
8. In another terminal, serve the frontend with
   `python -m http.server 8000 --directory frontend`, then open
   `http://localhost:8000/`.

### Visual preview (no database required)

Start the frontend server from the project directory with
`python -m http.server 8000 --directory frontend`, then open
`http://localhost:8000/?preview=1`. This interactive preview uses labeled sample
Kepler-90 records and does not read or modify MySQL. Add, edit, and NASA import
actions are disabled in preview mode.

Open `http://localhost:8000/scientist.html?preview=1` for the scientist workspace.
It uses all 4,048 PHL 2019 rows and local model estimates, with candidate ranking,
completeness, a flux/HZ diagram, ESI components, and an honest empty state for
historical drift (the sample CSV does not contain assessment history).

## Code organization

- `backend/routes/`: HTTP request and response handling.
- `backend/services.py`: validation and application workflow.
- `backend/repositories.py`: SQL queries and persistence operations.
- `backend/db.py`: pooled connections, transactions, and cursor cleanup.
- `backend/predictor.py`: saved model loading and inference.
- `model/feature_contract.py`: shared feature names and API-to-training mapping.
- `database/`: schema, triggers, stored procedures, and migration.

For the reasons behind the architecture and implementation sequence, including
tradeoffs and alternatives, see
[`docs/backend-improvement-learning-guide.md`](docs/backend-improvement-learning-guide.md).

See `docs/architecture-and-data-contract.md` for the request pipeline and the
database/model field contract.
