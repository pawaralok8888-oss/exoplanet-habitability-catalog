# Exoplanet Habitability Catalog: newcomer guide

Welcome! This project stores exoplanet and host-star catalog records, calculates an exploratory machine-learning score, and displays the data in a browser dashboard. It is a research-support and learning project: a high score is a model estimate, not evidence that a planet has life.

## What the project does

1. Reads catalog data from a processed PHL dataset and can request a small update from NASA's Exoplanet Archive.
2. Stores stars, planets, and prediction history in MySQL.
3. Serves data through a Flask JSON API.
4. Displays the catalog in a static HTML, CSS, and JavaScript website.
5. Uses a saved scikit-learn pipeline to estimate a habitability score when a planet is created or updated.

Main screens:

- frontend/index.html: planet explorer and catalog.
- frontend/scientist.html: research workspace for candidate ranking, ESI, habitable-zone position, input completeness, and score history.
- frontend/star-explorer.html: host-star view.

## Languages and technology

| Part | Language / technology | Role |
| --- | --- | --- |
| Browser content | HTML | Page content and controls. |
| Browser appearance | CSS | Layout, typography, color, responsive presentation. |
| Browser behavior | JavaScript | Calls the API, handles filters and selection, draws visuals. |
| API and application logic | Python, Flask | HTTP requests, validation, workflows, JSON responses. |
| Request validation | Pydantic | Checks incoming planet and star data. |
| Database | MySQL, SQL | Stores stars, planets, and score history. |
| Database driver | mysql-connector-python | Connects Python to MySQL; backend/db.py adds a connection pool and transaction helpers. |
| Data science | pandas, NumPy, scikit-learn | Reads tabular data, prepares features, trains and runs the classifier. |
| External catalog | NASA Exoplanet Archive TAP API | Optional source for a small batch of new records. |

## Where to start in the files

Use this nested project copy as the working copy. A similarly named project directory also exists at the parent level, so check the full folder path before running commands or editing.

| Path | Start here to understand… |
| --- | --- |
| README.md | Setup, run commands, folder map. |
| frontend/index.html | Main explorer page. |
| frontend/scientist.html | Scientist workspace page. |
| frontend/js/ and frontend/css/ | Browser behavior and styling. |
| backend/app.py | Flask app and API route registration. |
| backend/routes/ | HTTP endpoints for stars, planets, and NASA ingestion. |
| backend/schemas.py | Accepted fields and validation. |
| backend/services.py | Application workflow and model feature preparation. |
| backend/repositories.py | SQL statements and data operations. |
| backend/db.py | Pooled connections, commits/rollbacks, cursor cleanup. |
| backend/predictor.py | Loads and calls the saved model. |
| model/feature_contract.py | Ordered model inputs and field-name mapping. |
| model/train_model.py | Model training and evaluation. |
| model.pkl and model/metadata.json | Saved preprocessing/classifier and feature-contract metadata. |
| database/schema.sql | Main table definitions and relationship. |
| database/habitability_log.sql | Score-history table and triggers. |
| database/procedures.sql | Stored procedures, including prediction history. |
| database/load_data.py | Loads the processed PHL data into MySQL. |
| data/raw/ and data/processed/ | Source catalog and engineered CSV files. |
| .env | Local DB settings. Git-ignored; never commit or share its password. |

## Basic terms

- Frontend: the pages a person sees in the browser.
- API: URLs the frontend calls to request data or actions. This API exchanges JSON.
- Route: a URL and Python function that handles its HTTP request. For example, GET /api/exoplanets/ asks for planet rows.
- Service: application rules coordinating validation, prediction, and persistence.
- Repository: Python functions that run SQL reads and writes.
- Schema: database table definitions and relationships.
- Inference: using an already trained model to estimate an output for input values.
- Training: fitting a model using labeled data; separate from serving predictions.
- ESI: formula-based similarity to Earth, separate from the model score.
- Habitable zone (HZ): an estimated orbital region where liquid water may be possible under assumptions. HZ membership alone does not establish habitability.
- Drift/history: recorded model scores over time. A score change does not explain its own cause.

## Run locally

Prerequisites: Python packages from requirements.txt, MySQL, and a database initialized from the SQL files. Put database settings in the local .env or environment variables.

From this project directory:

1. Install dependencies: python -m pip install -r requirements.txt
2. For a new database, run database/schema.sql, database/habitability_log.sql, and database/procedures.sql, in that order. For an existing database, apply numbered migrations in database/migrations/ and then rerun database/procedures.sql.
3. Load or refresh the catalog: python database/load_data.py
4. Start the API in one terminal: python backend/app.py
5. Start the website in another: python -m http.server 8000 --directory frontend
6. Open http://127.0.0.1:8000/.

The API runs on port 5000. For a visual preview without a database, open http://127.0.0.1:8000/?preview=1. The scientist preview is http://127.0.0.1:8000/scientist.html?preview=1.

The Flask built-in server is for local development, not public deployment. Never commit .env, credentials, or production secrets.

## First code-reading exercise

Trace the scientist page's catalog search:

1. Browser JavaScript sends GET /api/exoplanets/search with paging and filter values.
2. backend/routes/exoplanets.py validates query parameters.
3. backend/repositories.py counts matching planets and runs a parameterized SQL query for one page.
4. backend/db.py borrows a pooled MySQL connection, executes the query, closes the cursor, and returns the connection to the pool.
5. Flask returns JSON; the page renders candidate rows.

Then trace a planet update to see validation, model feature mapping, prediction, database persistence, and score-history logging.

## Limits to remember

- The score is exploratory and is not a probability that life exists.
- The saved model imputes some missing inputs; the dashboard exposes completeness because imputed results have less direct observed support.
- NASA ingestion is a small synchronous demonstration, not a robust bulk-import pipeline.
- General list endpoints can return all rows; use paginated search when browsing a large catalog.
- The local setup is not a public production deployment. See production-readiness.md.

Continue with mentor-system-walkthrough.md for the full request path and a mentor-facing explanation.
