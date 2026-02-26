# Utilities

Database connection and helper utilities used across query and merge modules.

## Modules

| Module | Purpose |
|--------|---------|
| `db_connect.py` | PostgreSQL connection configuration. Reads from `.env` (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD). |
| `db_utils.py` | Connection pool, chunked query execution, CSV export, Medicaid ID lookup caching. |
