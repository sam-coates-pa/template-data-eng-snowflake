# ❄️ Snowflake Data Engineering Template

A practical, production‑minded template for building Snowflake‑native ELT pipelines using Snowpark, the Snowflake Python Connector, and Prefect 2.x orchestration.
It provides ready‑made patterns for internal stage ingestion, Snowpark transformations, table loading (MERGE / overwrite), environment‑driven config, and CI‑friendly project scaffolding.

> Use this as a GitHub Template Repository to proivde a fast, consistent starting point for Snowflake ELT delivery.


## What's Included

- **End‑to‑end ELT flow**: Extract → Stage → Snowpark Transform → Load Table
- **Core modules**: Session builder, staged file loader, Snowpark transformer, table loader
- **Extras**: Optional external S3 stages, dbt‑snowflake support, private key authentication
- **Dev experience**: Config files, Makefile, tests, CI workflow, .env.example, Prefect deploys



## Reference Architecture
```
Source → Extract (Python)
             │
             ▼
   Snowflake Stage (internal)
             │
             ▼
     Snowpark Transform (Python DF)
             │
             ▼
   Snowflake Table Load (MERGE / overwrite)
             │
             ▼
        Prefect Orchestration
```

## Project Layout (key folders)
```
flows/                          # Prefect flows
      full_pipeline.py

modules/                        # Session, loader, transformer modules
      connector.py
      loader.py
      transformer.py              

config/                         # dev/prod environment configs
      dev.yaml
      prod.yaml

.github/workflows/              # CI pipeline

.env.example                    # environment variable template

requirements.txt                # Python dependencies

Makefile                        # common developer commands
```


## Quick Start

- Create a new repo using “Use this template”.
- Populate .env using the provided .env.example (never commit real secrets).
- Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python flows/full_pipeline.py
```
(Optional) Prefect Cloud:

```bash
export PREFECT_API_URL=...export PREFECT_API_KEY=...prefect deploy --all
```
Option 1: Prefect Execution

Run locally
```bash
python flows/full_pipeline.py
```
(Optional) Deploy to Prefect Cloud
```bash
export PREFECT_API_URL="your_prefect_api_url"
export PREFECT_API_KEY="your_prefect_api_key"
prefect deploy --all
```
Option 2: Airflow Execution

Define your local Airflow home directory
```bash
export AIRFLOW_HOME=$(pwd)
```

Run the DAG locally (requires Airflow 2.5+ and dag.test() in script)
```bash
python dags/full_pipeline_dag.py
```

## Environment Variables
Place Snowflake credentials in .env or a dedicated env.snowflake.example.

### Snowflake Credentials
```
SNOWFLAKE_ACCOUNT=

SNOWFLAKE_USER=

SNOWFLAKE_PASSWORD=

SNOWFLAKE_ROLE=

SNOWFLAKE_WAREHOUSE=

SNOWFLAKE_DATABASE=

SNOWFLAKE_SCHEMA=
```


### Optional Private Key Auth
```
SNOWFLAKE_PRIVATE_KEY_PATH=

SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=
```


### Prefect (Optional)

Configure Prefect Cloud credentials if using managed orchestration:

```bash
PREFECT_API_URL=
PREFECT_API_KEY=
```

Run locally:

```bash
python flows/full_pipeline.py
```

Deploy to Prefect Cloud:

```bash
prefect deploy --all
```

## Prefect Flow Pattern (Simplified)

Example flow demonstrating a typical Snowflake ELT process:

```python
import os
import pandas as pd

from prefect import flow, task
from snowflake.snowpark import Session


def get_session():
    return Session.builder.configs(
        {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
        }
    ).create()


@task
def extract():
    return [
        {"id": 1, "value": 10},
        {"id": 2, "value": 30},
    ]


@task
def stage_to_snowflake(data):
    df = pd.DataFrame(data)

    df.to_json(
        "extract.json",
        orient="records"
    )

    session = get_session()

    session.file.put(
        "extract.json",
        "@MY_INTERNAL_STAGE/data",
        overwrite=True
    )

    return "@MY_INTERNAL_STAGE/data/extract.json"


@task
def transform(stage_file):
    session = get_session()

    df = session.read.json(stage_file)

    return df.with_column(
        "adjusted",
        df["VALUE"] * 1.5
    )


@task
def load(df):
    (
        df.write
        .mode("overwrite")
        .save_as_table(
            "ANALYTICS.TRANSFORMED_DATA"
        )
    )


@flow(name="full-snowflake-pipeline")
def full_pipeline():
    raw_data = extract()

    staged_file = stage_to_snowflake(raw_data)

    transformed_data = transform(staged_file)

    load(transformed_data)


if __name__ == "__main__":
    full_pipeline()
```

### Flow Pattern

```text
Extract
    ↓
Stage File
    ↓
Snowpark Transform
    ↓
Load Target Table
    ↓
Orchestrate & Monitor
```


---

### Airflow (Optional)

Configure Airflow to use a Snowflake connection (for example, `snowflake_default`) via **Admin → Connections**.

Example DAG using the same ELT pattern as the Prefect flow:

```python
from datetime import datetime

from airflow.decorators import dag
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

SNOWFLAKE_CONN_ID = "snowflake_default"

@dag(
    dag_id="snowflake-full-pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["snowflake", "elt"],
)
def snowflake_pipeline():

    stage_data = SnowflakeOperator(
        task_id="stage_data",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql="""
            COPY INTO RAW.EXTRACT_DATA
            FROM @MY_INTERNAL_STAGE/data/
            FILE_FORMAT = (
                TYPE = JSON
            );
        """,
    )

    transform_data = SnowflakeOperator(
        task_id="transform_data",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql="""
            CREATE OR REPLACE TABLE CURATED.TRANSFORMED_DATA AS
            SELECT
                id,
                value,
                value * 1.5 AS adjusted
            FROM RAW.EXTRACT_DATA;
        """,
    )

    publish_data = SnowflakeOperator(
        task_id="publish_data",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql="""
            CREATE OR REPLACE TABLE ANALYTICS.TRANSFORMED_DATA AS
            SELECT *
            FROM CURATED.TRANSFORMED_DATA;
        """,
    )

    stage_data >> transform_data >> publish_data


snowflake_pipeline_dag = snowflake_pipeline()
```

Run locally (Airflow 2.5+):

```bash
python dags/full_pipeline_dag.py
```

## Snowflake Session Configuration

Used by Snowpark and the Python Connector - maps directly to the environment variables above.
``` bash
PythonSession.builder.configs({    "account": SNOWFLAKE_ACCOUNT,    "user": SNOWFLAKE_USER,    "password": SNOWFLAKE_PASSWORD,    "role": SNOWFLAKE_ROLE,    "warehouse": SNOWFLAKE_WAREHOUSE,    "database": SNOWFLAKE_DATABASE,    "schema": SNOWFLAKE_SCHEMA,})
```

## Staging Conventions

Use internal stages for secure, fast ingestion.

Logical, predictable folder structure:
```bash
@my_stage/data/2026/01/01/
```

Store as JSON, CSV, or Parquet as needed.


## Transform (Snowpark)
Patterns:

- Schema enforcement via Snowpark DataFrames
- Column derivations
- UDF / Vectorised Python when required
- Hybrid SQL + Snowpark when useful

## Tips

- Use Snowpark for Python‑first teams.
- Prefer SQL for set‑based logic.
- Keep transformations deterministic and idempotent.


### Loading – MERGE or Overwrite

Two standard options:

1) Overwrite (full rebuild)
```bash
Pythondf.write.mode("overwrite").save_as_table("DB.SCHEMA.TABLE")
```

2) Incremental MERGE
Ideal for upserts and CDC‑style patterns.
```bash
MERGE INTO target t USING source s ON t.id = s.idWHEN MATCHED THEN UPDATE SET ...WHEN NOT MATCHED THEN INSERT (...);
```

### Modeling tips

- Separate staging, transform, and publish layers.
- Use clustering on large analytic tables.


## CI/CD (Optional)

Automate quality checks, testing, and deployment using GitHub Actions or your preferred CI/CD platform.

### Continuous Integration (CI)

Recommended validation steps on every pull request:

- Dependency installation
- Code formatting checks
- Linting
- Unit testing
- Security scanning (optional)

Example workflow:

```text
Pull Request
      ↓
Install Dependencies
      ↓
Lint (flake8)
      ↓
Format Check (black)
      ↓
Run Tests (pytest)
      ↓
Build Validation
      ↓
Merge Approval
```

Typical commands:

```bash
black --check .
flake8 .
pytest
```

---

### Continuous Deployment (CD)

Deploy Snowflake assets and orchestration code using:

- GitHub Actions
- Azure DevOps Pipelines
- GitLab CI/CD
- Jenkins

Deployment targets may include:

- Snowflake databases and schemas
- Snowpark applications
- SQL scripts
- Prefect deployments
- Airflow DAGs

Example deployment flow:

```text
Merge to Main
      ↓
Run CI Pipeline
      ↓
Deploy Snowflake Assets
      ↓
Deploy Orchestration
      ↓
Execute Smoke Tests
      ↓
Production Ready
```

---

### GitHub Actions Example

Example deployment workflow:

```yaml
name: Snowflake Deployment

on:
  push:
    branches:
      - main

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run Tests
        run: pytest

      - name: Deploy Snowflake Assets
        run: make deploy
```

---

### Prefect Deployments

Automatically deploy flows when changes are made to the `flows/` directory.

Example trigger:

```text
flows/**
```

Deploy command:

```bash
prefect deploy --all
```

Recommended workflow:

```text
Code Change
      ↓
CI Validation
      ↓
Flow Deployment
      ↓
Prefect Work Pool
      ↓
Scheduled / Triggered Execution
```

---

### Makefile Targets

Common deployment commands:

```bash
make install
make lint
make format
make test
make deploy
```

Example:

```Makefile
install:
    pip install -r requirements.txt

lint:
    flake8 .

format:
    black .

test:
    pytest

deploy:
    prefect deploy --all
```

---

### Recommended Pipeline Gates

Before deployment to Production:

- ✅ All tests passing
- ✅ Pull request approved
- ✅ No critical security vulnerabilities
- ✅ Environment configuration validated
- ✅ Snowflake connectivity verified
- ✅ Deployment smoke tests successful

This helps ensure deployments are repeatable, traceable, and production-ready.


## Architecture Principles

This template follows several key engineering principles:

- **ELT-first**: Load raw data before applying business transformations.
- **Idempotent pipelines**: Re-running a pipeline should not produce duplicate results.
- **Configuration-driven**: Environment-specific settings remain outside application code.
- **Cloud-native processing**: Push computation into Snowflake wherever possible.
- **Reproducible deployments**: Infrastructure, code, and configuration should be version controlled.
- **Observability by default**: Logging, monitoring, and alerting built into orchestration.

---

## Recommended Data Layering

A Medallion-style architecture works well for most Snowflake implementations:

```text
RAW
 └── Landed source data

STAGING
 └── Standardised schema and data types

CURATED
 └── Business transformations and enrichment

PRESENTATION
 └── Reporting, analytics and downstream consumption
```

Example naming:

```text
RAW.CRM.CUSTOMERS
STG.CRM.CUSTOMERS
CURATED.CUSTOMERS
PRESENTATION.CUSTOMER_ANALYTICS
```

### Benefits

- Improved traceability
- Simplified troubleshooting
- Clear ownership boundaries
- Reusable transformation logic

---

## Snowflake Streams & Tasks (Optional)

For near real-time or incremental processing, Snowflake Streams and Tasks can complement Prefect or Airflow.

### Stream Example

```sql
CREATE STREAM CUSTOMER_STREAM
ON TABLE RAW.CUSTOMERS;
```

### Task Example

```sql
CREATE TASK PROCESS_CUSTOMERS
WAREHOUSE = COMPUTE_WH
SCHEDULE = 'USING CRON 0 * * * * UTC'
AS
MERGE INTO CURATED.CUSTOMERS t
USING (
    SELECT * FROM CUSTOMER_STREAM
) s
ON t.CUSTOMER_ID = s.CUSTOMER_ID
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT (...);
```

Use Streams and Tasks when:

- Low-latency ingestion is required
- CDC processing is needed
- Transformations can execute entirely within Snowflake

---

## dbt Integration

This template can be extended with dbt for SQL-first transformation development.

### Installation

```bash
pip install dbt-snowflake
```

### Example Project Structure

```text
dbt/
├── models/
│   ├── staging/
│   ├── intermediate/
│   └── marts/
├── tests/
└── dbt_project.yml
```

### Execution

```bash
dbt run
dbt test
```

A common orchestration pattern:

```text
Prefect/Airflow
      ↓
Load Raw Data
      ↓
dbt Run
      ↓
Publish Analytics Models
```

---

## Secrets Management

Avoid storing credentials in source code.

### Recommended Solutions

- Azure Key Vault
- AWS Secrets Manager
- HashiCorp Vault
- GitHub Actions Secrets
- Prefect Blocks

Example:

```python
password = os.getenv("SNOWFLAKE_PASSWORD")
```

Never commit:

```text
.env
*.pem
*.p8
private_key.*
```

Add the following to `.gitignore`:

```text
.env
.env.*
*.pem
*.p8
```

---

## Branching Strategy

Suggested Git workflow:

```text
main
 ├── develop
 │
 ├── feature/add-customer-pipeline
 ├── feature/new-snowpark-transform
 └── hotfix/fix-merge-issue
```

### Guidelines

- Protect the `main` branch.
- Require pull request approvals.
- Require CI checks before merge.
- Tag production releases.

Example semantic versioning:

```text
v1.0.0
v1.1.0
v2.0.0
```

---

## Cost Optimisation

Snowflake is highly scalable, but good governance prevents unnecessary spend.

### Recommendations

- Enable warehouse auto-suspend.
- Use appropriately sized warehouses.
- Optimise large joins and aggregations.
- Use clustering selectively.
- Remove unused stages and transient data.
- Monitor expensive queries using Query History.

Example:

```sql
ALTER WAREHOUSE COMPUTE_WH
SET AUTO_SUSPEND = 60
AUTO_RESUME = TRUE;
```

---

## Logging & Observability

Every pipeline should emit structured logs.

### Recommended Metadata

```text
Pipeline Name
Execution ID
Source System
Rows Extracted
Rows Loaded
Execution Duration
Error Details
```

Example:

```python
logger.info(
    "Loaded %s records into %s",
    row_count,
    target_table
)
```

Track metrics such as:

- Pipeline execution time
- Data freshness
- Load volumes
- Failure rates
- Credit consumption

---

## Troubleshooting

### Authentication Errors

Verify the following values are populated correctly:

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
```

Check connectivity:

```sql
SELECT CURRENT_USER();
SELECT CURRENT_ROLE();
SELECT CURRENT_WAREHOUSE();
```

### Stage Upload Failures

Confirm stages exist:

```sql
SHOW STAGES;
```

Check:

- Stage permissions
- File permissions
- Storage integrations
- Maximum file sizes

### Warehouse Errors

Verify warehouse availability:

```sql
SHOW WAREHOUSES;
```

Confirm role grants:

```sql
SHOW GRANTS TO ROLE <ROLE_NAME>;
```

---

## Production Deployment Recommendations

For enterprise-scale implementations:

- Separate Development, Test, and Production environments.
- Use dedicated Snowflake roles per environment.
- Deploy exclusively through CI/CD pipelines.
- Store infrastructure as code where possible.
- Implement automated rollback procedures.
- Enable monitoring and alerting prior to go-live.
- Document operational support procedures.

Example environment separation:

```text
DEV_DATABASE
TEST_DATABASE
PROD_DATABASE
```

### Recommended Promotion Path

```text
Developer Branch
        ↓
Development
        ↓
Test / UAT
        ↓
Production
```

---

## Security Best Practices

### Principle of Least Privilege

Grant only the permissions required by pipelines and users.

Example:

```sql
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE ETL_ROLE;

GRANT USAGE ON DATABASE ANALYTICS TO ROLE ETL_ROLE;

GRANT SELECT, INSERT, UPDATE
ON ALL TABLES IN SCHEMA ANALYTICS.CURATED
TO ROLE ETL_ROLE;
```

### Service Accounts

Use dedicated service users for automated workloads:

```text
svc_prefect_prod
svc_airflow_prod
svc_github_actions
```

Benefits:

- Clear auditing
- Reduced operational risk
- Easier access reviews

---

## Repository Standards

Recommended structure for production projects:

```text
.
├── config/
├── dags/
├── flows/
├── modules/
├── sql/
├── tests/
├── docs/
├── scripts/
├── .github/
└── README.md
```

## Testing & Quality

Unit tests for session, loader, transformer modules

Data tests: schema + row count checks

Pre‑commit: flake8, black, pytest


## Operations

Observe via Prefect logs, Snowflake query history

Cost controls: warehouse size, auto‑suspend, clustering

Monitoring failures: Prefect alerts, Slack/SNS integrations


## Checklist Before Production

 - Roles & least‑privilege permissions
 - Warehouse auto‑suspend & sizing rules
 - Proper stage cleanup strategy
 - Error handling & retries in flows
 - Clear staging → transform → publish layers
 - Secret management (no hard‑coded passwords)
 -  CI pipelines passing


## License & Contributions
PA’s standard licensing — PRs welcome for additional patterns (MERGE helpers, dbt models, Streams/Tasks orchestration, external stage ingestion, etc.).
