# Backend improvement tasks: learning guide

This guide records the changes in this project copy and explains why they were done, how they fit together, what can go wrong if they are skipped, and when an alternative would be a better choice. It describes the implementation currently in this repository; it is not a list of work to do manually.

## The request path we are building

```text
Browser page
  → Flask route (HTTP and query parameters)
  → service (validation and business workflow)
  → repository (SQL statements)
  → db helper (pooled connection and cursor cleanup)
  → MySQL
```

For predictions, the service also calls the predictor, which checks the saved model's feature metadata before inference. This separation makes it easier to understand where a bug belongs: HTTP formatting belongs in a route, input rules in a schema, business coordination in a service, and SQL in a repository.

## Tasks completed in sequence

### 1. Establish the project copy and data contracts

**Files:** `docs/architecture-and-data-contract.md`, `docs/scientist-data-contract.md`, `database/schema.sql`, `database/migrations/`

We compared the two repository copies and kept them separate, as requested. The active improvements are in this nested project copy. The architecture/data contract documents the actual table and column names, model feature order and units, and the schema/migration sequence. This prevents the older alternative schema and procedure scripts from being mistaken for the running application's contract.

**Why first:** Every later layer needs to agree on names, units, and ownership. A route cannot safely validate `planet_name` if the live table uses `name`; the model cannot use orbital distance as stellar flux.

**If skipped:** SQL may target nonexistent columns, features may use the wrong physical quantity, or migrations may be applied in the wrong order.

**Alternative:** Generate contracts from a formal OpenAPI schema and migration tool. That is more automated, but requires adopting and maintaining those tools. The current project uses concise Markdown plus SQL scripts because the schema is small.

### 2. Centralize database connections and transactions

**Files:** `backend/db.py`, `backend/repositories.py`

`db.py` owns the MySQL connection pool, commit/rollback boundary, and explicit cursor cleanup. Repository functions call these helpers rather than opening a connection in every route. SQL remains parameterized, which separates values from SQL syntax and avoids hand-built value interpolation.

**Why before service/route cleanup:** A repository needs one reliable way to run SQL; services and routes can then use those repository functions without managing cursor lifetimes.

**If skipped:** Connections/cursors can leak, transaction behavior becomes inconsistent, and database changes are harder to inspect or reuse.

**Alternative:** SQLAlchemy offers ORM mappings, query composition, and mature migration integration. For this compact relational schema with existing SQL and stored procedures, a small DAO/repository using `mysql.connector` is simpler. Reconsider SQLAlchemy if relationships and migrations become significantly more complex.

### 3. Add request schemas and use them through services

**Files:** `backend/schemas.py`, `backend/services.py`, `backend/requirements.txt`, `requirements.txt`

Pydantic schemas describe accepted planet/star fields, types, bounds, extra-field policy, whitespace trimming, and blank optional text normalization. Services validate incoming data with those schemas and coordinate persistence and prediction; routes convert known validation failures into HTTP 400 responses. Dependency files include the libraries used by the application.

**Why after defining the data contract:** Validation rules should describe the actual fields and units in the database/model contract. Services are the place to use validated values before doing work.

**If skipped:** Bad types, impossible values, misspelled keys, and blank strings can flow into SQL or model inference and cause confusing failures or invalid records.

**Alternative:** Marshmallow provides schemas and serialization; Flask-WTF suits form/CSRF workflows. Pydantic works well here because the project needs straightforward typed JSON validation and already targets Python 3.10+ style typing.

### 4. Keep route, service, repository, and prediction responsibilities distinct

**Files:** `backend/routes/*.py`, `backend/services.py`, `backend/repositories.py`, `backend/predictor.py`

Routes parse HTTP inputs and shape responses. Services validate and coordinate operations. Repositories own SQL. The predictor owns model loading and scoring. The shared `backend/db.py` owns connection behavior. This is a lightweight layered design, not a new framework.

**Connection to the previous tasks:** Schemas need a consistent caller (services), and services need a consistent persistence interface (repositories). With those pieces, routes can stay focused on HTTP concerns.

**If skipped:** One route can become a large block mixing request parsing, validation, SQL, model inference, and response formatting; then a small change risks breaking unrelated behavior and is harder to explain or review.

**Alternative:** A larger application could use a Flask application factory, dependency injection, and more formal domain modules. The current layout is enough for the prototype and can grow gradually.

### 5. Make the model feature contract explicit and version-check it

**Files:** `model/feature_contract.py`, `model/train_model.py`, `model/metadata.json`, `backend/predictor.py`, `model.pkl`

The feature contract holds the canonical feature order and contract version. Training saves a preprocessing-plus-classifier pipeline and writes metadata containing its model version, feature contract version, feature columns, and training timestamp. Prediction loads the metadata and refuses a mismatched feature contract. The saved pipeline contains the median imputer, so inference applies the same learned imputation used during training. The API's `stellar_flux` maps to training feature `P_FLUX`; `orbital_distance` does not.

**Why before serving predictions:** Training and inference must interpret each feature identically. Metadata catches incompatible artifacts before silently producing misleading scores.

**If skipped:** A model may receive reordered or semantically different features, or missing values may be treated differently between training and inference.

**Alternative:** Persist a richer model card and use MLflow/model registry for artifact lineage, versioning, and deployment. That is useful for team deployments and multiple models; local pickle plus JSON is smaller for a classroom prototype. Pickle files must only be loaded from trusted project artifacts.

**Interpretation limit:** The most recent training output had only 11 positive examples in its test split. Perfect reported metrics on so few positives do not establish robust performance. Evaluate more independent positive cases, precision/recall, calibration, and ranking usefulness before scientific or operational claims.

### 6. Restrict browser CORS to the intended local frontend

**File:** `backend/app.py`

CORS is configured only for `/api/.*` and the two local frontend origins (`localhost:8000` and `127.0.0.1:8000`). Flask debug mode is off by default and enabled only with `FLASK_DEBUG=1`.

**Why now:** Once the API contract and frontend calls are clear, browser access can be limited to the expected local development origins.

**If skipped:** Any website can attempt browser-based cross-origin reads from a visitor's browser. CORS is not authentication and does not block command-line clients.

**Alternative:** In production, serve UI and API on one origin behind a reverse proxy, or explicitly configure the deployed UI origin. Add authentication and authorization for protected operations; CORS alone does not secure an API.

### 7. Add server-side filters and pagination to the scientist catalog

**Files:** `backend/routes/exoplanets.py`, `backend/repositories.py`, `frontend/js/scientist.js`, `frontend/scientist.html`

`GET /api/exoplanets/search` accepts `page`, `per_page`, `q`, `hz`, `score`, and `drift_only`. It validates ranges and allowed values, then returns an envelope with `items`, `page`, `per_page`, `total`, and `pages`. Repository SQL applies parameterized filters, counts the same matching set, orders deterministically, and returns one bounded page. The existing `GET /api/exoplanets/` still returns the full catalog for the main catalog screen, whose star-system visualization expects the full set. The scientist dashboard requests 12 results per page and requests stars/drift IDs once rather than once per planet. Preview mode continues to filter its local sample in the browser.

**Connection to earlier tasks:** Routes validate query parameters, repository helpers construct SQL, and the UI consumes the documented response shape. The count and page queries share the same filter builder so the total describes the results being shown.

**If skipped:** The browser downloads every record for a table view, increasing transfer, memory, and render work as the catalog grows. Client-only filtering cannot efficiently retrieve a later subset without first downloading the catalog. The old one-request-per-planet drift pattern would also create N+1 network traffic.

**Frontend impact:** It now displays total matches and a page summary; search/filter changes return to page one; Previous/Next request the adjacent page. Scientist charts that use catalog rows represent the current result page in live mode, so their notes disclose that scope. The main catalog keeps its existing all-record response.

**Alternative:** Cursor/keyset pagination is more efficient for very large, frequently changing tables than `LIMIT/OFFSET`, but is more complex and awkward for jumping to a numbered page. Offset pagination is reasonable at this project's current scale. A dedicated chart aggregate endpoint could summarize all filtered results without downloading every row if whole-result analytics become necessary.

### 8. Keep the current UI, database, and import choices proportional to the project

**Frontend:** The static HTML/JavaScript dashboard remains appropriate for the current small number of screens. React/Next.js becomes useful when shared interactive components, client-side routing, or complex state grow enough to justify a build system and framework.

**Database:** MySQL remains appropriate because the data is relational: stars own planets and planets have prediction history. PostgreSQL is also a strong relational alternative, but switching provides little benefit unless deployment, SQL features, or team requirements call for it. MongoDB would make the core relationships and joins less natural.

**NASA import:** The import route remains synchronous and manually triggered, with a bounded external request in the existing implementation. A scheduled/background job (for example, a task queue) is a better next step if imports become slow, frequent, retried, or too long for an HTTP request. Background processing adds operational components, so it is not automatically more efficient for a small one-off import.

**Security/deployment:** The project remains a local prototype. Before public deployment, add authentication/authorization, production server configuration, secrets management, stronger operational logging, and deployment-specific CORS. Turning off debug by default and restricting CORS reduce avoidable local risks but do not replace these controls.

## How the tasks depend on one another

```text
Database/model contract
  → database helper and repository
  → schemas and services
  → thin HTTP routes
  → validated search/count/page endpoint
  → dashboard pagination and chart scope

Feature contract
  → training pipeline + metadata
  → predictor compatibility check
  → service prediction
```

The first chain makes data requests predictable from storage through the screen. The second makes a model score interpretable and compatible from training through prediction. CORS controls which browser origins can call the API; it sits at the web boundary and complements, but does not replace, authentication.

## Manual inspection path

For a guided code review, open these files in order:

1. `docs/architecture-and-data-contract.md` — system path and shared names/units.
2. `backend/db.py` — connection, transaction, and cleanup helper.
3. `backend/repositories.py` — database queries, including filtered page queries.
4. `backend/schemas.py` then `backend/services.py` — input rules and use of validated data.
5. `backend/routes/exoplanets.py` — HTTP inputs and the pagination response.
6. `model/feature_contract.py`, `model/train_model.py`, and `backend/predictor.py` — consistent model inputs and artifact checks.
7. `frontend/js/scientist.js` and `frontend/scientist.html` — how the page requests, displays, and navigates those results.

The work was reviewed by reading the changed interfaces and comparing caller/callee names and response fields. Automated tests and a live MySQL/browser run have not been performed as part of this implementation pass; the endpoint should be exercised against a database with the documented schema before a live demonstration.
