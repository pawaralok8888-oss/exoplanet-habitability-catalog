# Production readiness and improvement roadmap

This is a student/research prototype with a useful separation of concerns. The current local setup should not yet be called production grade.

## Already in place

- Flask JSON API and static browser frontend.
- Pydantic validation for planet and star input.
- Service/repository split and parameterized SQL.
- MySQL connection pool and cursor/transaction helpers.
- Saved scikit-learn preprocessing-plus-classifier pipeline.
- NASA TAP records use the same validation, ESI calculation, inference, and model-version stamping as API-created planets.
- Assessment logs retain old/new scores, changed planet fields, data source, and model version.
- Paginated filtered search for the scientist catalog.
- Score-history logging and visible missing-input context.
- Local settings via environment variables or git-ignored .env.

## Incomplete or missing

- Authentication and authorization.
- Production WSGI deployment, HTTPS, and supervised processes.
- Pagination on every catalog-list endpoint.
- Asynchronous, retryable, auditable bulk ingestion.
- Shared transactions for multi-step operations.
- Structured logs, metrics, health checks, alerting.
- Automated test suite and documented backup/restore.
- Representative model validation for scientific interpretation.
- Extend the field-level audit trail to host-star observation changes and source record identifiers.

## Phased plan

### Phase 1 — Protect data and standardize the API

- Add authentication and roles, especially for writes and imports.
- Restrict CORS to deployment origins.
- Use a least-privilege DB user and keep secrets out of source control/logs.
- Set request-size and rate limits.
- Standardize errors and paginate/bound all list responses.

### Phase 2 — Reliable data changes and imports

- Use schema migrations as the supported upgrade path.
- Define transaction scopes for multi-step application operations.
- Move NASA ingestion to a background worker with retries, idempotency, resumable batches, and job status.
- Validate/quarantine malformed data and record source, retrieval time, and source identifiers.
- Document backups and test a restore.

### Phase 3 — Operate the service

- Serve Flask through production WSGI behind HTTPS.
- Add structured logs, request IDs, health/readiness endpoints, metrics, and error reporting.
- Pin/review dependencies; add environment-specific configuration and deployment automation.
- Add database integration tests and browser checks for core flows.

### Phase 4 — Defensible scientific results

- Evaluate with enough independent positive and negative examples; report precision, recall, PR-AUC, calibration, and uncertainty.
- Do not present the score as probability of life unless its calibration and meaning are established.
- Version datasets, features, model artifacts, and evaluation results together.
- Track old/new field values, source, time, and model version for each assessment. Planet inputs and model-version changes are now recorded; host-star field changes remain to be connected.
- Document assumptions/uncertainty in ESI and habitable-zone calculations.

## Acceptance principle

Call the service production ready only after security, reliability, deployment, and scientific review have explicit acceptance criteria and have been verified in the target environment. A running local demo is not sufficient.
