# tool-sql-select-extractor

Extracts SQL SELECT query results from PostgreSQL, MySQL, or SQLite databases as CSV.

SqlSelectExtractor is a **Extractor** that connects to a configured SQL database and executes
a **single read-only SELECT** statement. The query result is exported as a CSV table.

## What this tool does

- Connects to a database (**postgres**, **mysql**, or **sqlite**).
- Validates the query to allow **only** `SELECT` or `WITH ... SELECT`.
- Blocks write/DDL statements and multi-statement execution.
- Executes the query and exports the result as CSV.

## Security model (SELECT-only)

The tool rejects queries that:

- do not start with `SELECT` or `WITH`
- contain write/DDL keywords (e.g., `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`,
  `TRUNCATE`, …)
- contain risky patterns like `SELECT ... INTO` or `FOR UPDATE`
- contain multiple statements (only a single optional trailing `;` is allowed)

> Note: This is a pragmatic guardrail, not a formal SQL parser. It is designed to block common
> unsafe patterns in a simple, maintainable way.

## Configuration (Hyperparameters)

- `sql_distribution`: `postgres` | `mysql` | `sqlite`
- `host`: database host (ignored for sqlite)
- `port`: database port (ignored for sqlite)
- `database`: database name (or sqlite file path / `:memory:`)
- `username`: DB username
- `password`: DB password
- `sql_select`: single SELECT statement

## Outputs

- `dataset` (CSV): query result

## Python dependencies

This tool uses **pandas** and **SQLAlchemy**. Database drivers depend on your `sql_distribution`:

- Postgres: `psycopg2-binary`
- MySQL: `pymysql`
- SQLite: built-in (no extra driver)

A minimal `requirements.txt` looks like:

- pandas
- sqlalchemy
- psycopg2-binary
- pymysql

## Example SQL SELECT

Example (Postgres) to fetch a small subset, can be started with `example-database-compose.yml`

```sql
SELECT id, patient_code, age, bmi, created_at
FROM patients
WHERE age >= 50
ORDER BY created_at DESC LIMIT 10;
```

Example with aggregation:

```sql
SELECT COUNT(*) AS n,
       AVG(age) AS avg_age,
       AVG(bmi) AS avg_bmi
FROM patients;
```

### Suggested config values for the compose setup

Use these hyperparameters against the compose database:

- `sql_distribution`: `postgres`
- `host`: `postgres` *(if running from another container in same compose network)* **or**
  `localhost` *(if running locally on your host)*
- `port`: `5432` within the Compose network, or `5732` from the host
- `database`: `demo`
- `username`: `demo`
- `password`: `demo`
- `sql_select`: (use one of the examples above)

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Set APP_ID and platform URLs in .env before connecting.
python main.py
```

The Docker base image provides the FL-Net API. `requirements.txt` contains only
additional runtime dependencies; `requirements-dev.txt` includes the API for local development.

Build with `docker build -t tool-sql-select-extractor .`.
The sample database in `initdb/001_seed.sql` generates synthetic demo records.
