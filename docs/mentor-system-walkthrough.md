# Mentor guide: system inside-out

## Purpose and boundaries

The project combines relational data management, a JSON API, a browser dashboard, and an exploratory classifier. It helps users inspect catalog evidence and model estimates. It does not determine whether life exists.

## Architecture in one line

Browser (HTML/CSS/JavaScript) → HTTP/JSON → Flask routes → services → repositories → MySQL

The service calls the saved scikit-learn pipeline for prediction. NASA TAP ingestion is a separate route that contacts an external catalog and persists new rows.

## Component responsibilities

| Component | Responsibility | Implementation |
| --- | --- | --- |
| Presentation | Render explorer, filters, selected planet, plots, status. | frontend HTML, CSS, JavaScript |
| API/routing | Translate HTTP method, URL, query/body into JSON response and status. | Flask blueprints in backend/routes/ |
| Validation/workflow | Validate payloads, look up host-star inputs, map features, coordinate create/update. | backend/schemas.py and backend/services.py |
| Data access | Parameterized SQL for catalog CRUD, search, drift data, imports. | backend/repositories.py |
| Connection/transaction helper | Pooling, commit/rollback, cursor cleanup. | backend/db.py |
| Persistence | Stars, planets, prediction history. | MySQL tables, trigger, view, procedures |
| Model | Impute missing inputs and estimate positive-class probability. | model/train_model.py, model.pkl, backend/predictor.py |
| Ingestion | Load PHL rows; optionally fetch NASA TAP records. | database/load_data.py, backend/routes/fetch.py |

## Request pipeline

### Read and filter scientist catalog

1. JavaScript requests GET /api/exoplanets/search?page=1&per_page=12 and optional filters.
2. The Flask route validates page size and filter values.
3. The repository counts matches and executes parameterized SQL with LIMIT and OFFSET.
4. The DB helper executes using a pooled connection and closes its cursor.
5. Flask returns {items, page, per_page, total, pages} as JSON.
6. The browser renders rows and requests selected-planet history for the timeline.

Relevant files: frontend/js/, backend/routes/exoplanets.py, backend/repositories.py, backend/db.py.

### Create or update a planet

1. Browser submits JSON to POST /api/exoplanets/ or PUT /api/exoplanets/<planet_id>.
2. Route calls the service; Pydantic models reject unknown fields and invalid basic values.
3. If star_id is supplied, service reads that star and adds its temperature, radius, and mass to the model row.
4. model/feature_contract.py maps application names into the fixed training feature order.
5. backend/predictor.py checks model metadata, loads the saved pipeline, and gets the class-1 probability.
6. Repository writes the planet and score.
7. Database trigger records a history row on insert or when the score changes.
8. Route returns JSON and an HTTP status code.

The split keeps HTTP parsing, business workflow, SQL, and prediction in separate modules. However, each repository helper owns its own transaction. A workflow spanning multiple repository calls is not automatically one atomic transaction.

### Import NASA records

POST /api/fetch-new calls NASA TAP with a ten-second timeout, asks for at most five rows, skips names already present, inserts the rest, then returns a count. Network and DB work currently happen during the request. This is simple for a demo but not durable or resumable bulk ingestion.

## Database model

- stars: host-star properties and conservative habitable-zone bounds. star_id is the primary key.
- exoplanets: planet measurements, derived fields, source, and current predicted score. planet_id is the primary key. star_id is nullable and references stars; deleting a star sets it to NULL.
- habitability_log: one row per assessment event with a timestamp. Deleting a planet cascades to its history.

database/habitability_log.sql defines triggers that record initial assessments and changes to model inputs or score. GetDriftHistory returns ordered history including old/new scores, changed fields, source, model version, and timestamp. The dashboard uses a 0.15 adjacent-score-change threshold; this is a project alert setting, not a scientifically calibrated boundary.

database/load_data.py maps source PHL names into application/database names. Missing and sentinel physical measurements are stored as SQL NULL. The database field is name rather than source field P_NAME.

## Model and scientific interpretation

Training reads data/processed/exoplanets_features.csv. P_HABITABLE classes 1 and 2 become the positive class. A stratified train/test split is used. The saved scikit-learn pipeline applies median imputation and a class-weighted Random Forest with 200 trees; model.pkl stores both.

The fixed feature order is in model/feature_contract.py: ESI, HZ flag, planet radius, mass, equilibrium temperature, period, stellar flux, and host-star temperature/radius/mass. P_FLUX means incident stellar flux; orbital distance is a separate quantity and must not substitute for flux.

- The output is the model's positive-class probability, not a calibrated probability of life.
- ESI is a separate formula-based similarity, not the model score.
- HZ status is an indicator with assumptions and uncertainty.
- Missing model inputs may be imputed; completeness must be shown with the result.
- A score timeline shows changes in output, not their physical cause.
- Accuracy alone is inadequate for imbalanced classes. The current scientist page notes only 11 positive examples in the held-out test set; this is not enough to establish reliable ranking or calibration.

## API surface

| Method and path | Purpose |
| --- | --- |
| GET / | Basic API-running response. |
| GET /api/stars/ and GET /api/stars/<id> | List or retrieve stars. |
| POST /api/stars/, PUT /api/stars/<id>, DELETE /api/stars/<id> | Star CRUD. |
| GET /api/exoplanets/ | Full planet list; not paginated. |
| GET /api/exoplanets/search | Paginated search and filters. |
| GET /api/exoplanets/drifted?threshold=0.15 | Planets with score changes above the threshold. |
| GET /api/exoplanets/<id>/drift | One planet's assessment history. |
| POST /api/exoplanets/, PUT /api/exoplanets/<id>, DELETE /api/exoplanets/<id> | Planet CRUD; create/update run inference. |
| POST /api/fetch-new | Synchronous NASA TAP import demonstration. |

## Engineering assessment

### Strengths

- Clear separation among routes, schemas, services, repositories, DB helper, and predictor.
- Parameterized SQL and pooled connections with cursor cleanup.
- Basic payload validation and explicit handling for common input, missing-record, and model errors.
- Shared feature contract keeps training and inference field order aligned.
- Paginated scientist search, history, provenance, and visible missing-input context.

### Work needed before production

1. Identity and authorization: no authentication/role checks are evident in routes; define who can read, import, edit, or delete.
2. Production serving: app.run() is the development server. Use production WSGI, HTTPS/reverse proxy, configuration, and process supervision.
3. API consistency: general list endpoints return the entire catalog while scientist search is paginated. Bound and paginate every list route.
4. External imports: use a background job with retries, idempotency, import status, validation, and source-version metadata.
5. Atomic workflows: establish a shared transaction boundary when several reads/writes must succeed or fail together.
6. Observability: structured logs, request IDs, health/readiness checks, metrics, monitoring; never log credentials.
7. Operations: repeatable migrations, verified backup/restore, retention, deployment config, and secrets management.
8. Scientific validity: validate units/ranges and derivations; evaluate on a larger independent representative set and assess calibration before claiming calibrated probabilities.
9. Model lifecycle/security: version data/features/model and evaluation reports; define retraining/rollback; load only trusted pickle artifacts.
10. Testing: unit tests for schemas/features/services, MySQL integration tests for CRUD/triggers/transactions, and browser checks.
11. Auditability: record changed fields with old/new values, source, actor, and model version to explain drift.
12. Hardening: review deployment CORS origins, request size/rate limits, dependencies, and least-privilege DB credentials.

Production grade is a target, not a claim that this local project already meets. Prioritize access control, production serving, robust imports, migrations/backups, observability, and representative model validation.

## Suggested mentor demo

1. Introduce four research questions: Earth similarity, habitable-zone position, score trust/completeness, and score change.
2. Show candidate search and explain its paginated API response.
3. Select a planet; trace browser → route → repository → MySQL.
4. Explain ESI and ML output as separate signals; show missing inputs and evaluation caveat.
5. Show timeline and note the current history cannot explain causal field changes.
6. Walk through create/update: validation → feature mapping → inference → SQL → trigger history.
7. Close with roadmap: authorization, deployment, background import, stronger evaluation, audit, and operations.

## Backend fundamentals connection

The project demonstrates foundations such as HTTP, routing, validation, persistence, and model work. Security, scaling, queues, and observability are also useful concepts to discuss as gaps and future work. The referenced [Sriniously site](https://www.sriniously.com/) describes its backend series as covering HTTP, routing, authentication, databases, caching, queues, observability, scaling, security, and deployment. This guide maps those topics to the code; it does not imply endorsement or complete implementation.
