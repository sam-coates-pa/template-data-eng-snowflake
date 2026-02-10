# ❄️ Snowflake Full ELT Template

A practical, production‑minded template for building Snowflake‑native ELT pipelines using Snowpark, the Snowflake Python Connector, and Prefect 2.x orchestration.
It provides ready‑made patterns for internal stage ingestion, Snowpark transformations, table loading (MERGE / overwrite), environment‑driven config, and CI‑friendly project scaffolding.

Use this as a GitHub Template Repository to give teams a fast, consistent starting point for Snowflake ELT delivery.


## What's Included

End‑to‑end ELT flow: Extract → Stage → Snowpark Transform → Load Table
Core modules: Session builder, staged file loader, Snowpark transformer, table loader
Extras: Optional external S3 stages, dbt‑snowflake support, private key authentication
Dev experience: Config files, Makefile, tests, CI workflow, .env.example, Prefect deploys


## Reference Architecture
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


## Project Layout (key folders)
flows/                          # Prefect flows
src/snowflake/                  # Session, loader, transformer modules
config/                         # dev/prod environment configs
.github/workflows/              # CI pipeline
.env.example                    # environment variable template
requirements.txt                # Python dependencies
Makefile                        # common developer commands


## Quick Start

Create a new repo using “Use this template”.
Populate .env using the provided .env.example (never commit real secrets).
Install dependencies:

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

## Environment Variables
Place Snowflake credentials in .env or a dedicated env.snowflake.example.

### Snowflake Credentials

SNOWFLAKE_ACCOUNT= ,
SNOWFLAKE_USER= ,
SNOWFLAKE_PASSWORD=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=


### Optional Private Key Auth

SNOWFLAKE_PRIVATE_KEY_PATH=
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=


### Prefect (optional)

PREFECT_API_URL=
PREFECT_API_KEY=


## Snowflake Session Configuration
Used by Snowpark and the Python Connector—maps directly to the environment variables above.
PythonSession.builder.configs({    "account": SNOWFLAKE_ACCOUNT,    "user": SNOWFLAKE_USER,    "password": SNOWFLAKE_PASSWORD,    "role": SNOWFLAKE_ROLE,    "warehouse": SNOWFLAKE_WAREHOUSE,    "database": SNOWFLAKE_DATABASE,    "schema": SNOWFLAKE_SCHEMA,})Show more lines

## Prefect Flow Pattern (simplified)
``` bash
from prefect import flow, taskfrom snowflake.snowpark import Sessionimport pandas as pdimport osdef get_session():    return Session.builder.configs({        "account": os.getenv("SNOWFLAKE_ACCOUNT"),        "user": os.getenv("SNOWFLAKE_USER"),        "password": os.getenv("SNOWFLAKE_PASSWORD"),        "role": os.getenv("SNOWFLAKE_ROLE"),        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),        "database": os.getenv("SNOWFLAKE_DATABASE"),        "schema": os.getenv("SNOWFLAKE_SCHEMA"),    }).create()@taskdef extract():    return [{"id": 1, "value": 10}, {"id": 2, "value": 30}]@taskdef stage_to_snowflake(data):    df = pd.DataFrame(data)    df.to_json("extract.json", orient="records")    session = get_session()    session.file.put("extract.json", "@my_internal_stage/data", overwrite=True)    return "@my_internal_stage/data/extract.json"@taskdef transform(stage_file):    session = get_session()    df = session.read.json(stage_file)    return df.with_column("adjusted", df["value"] * 1.5)@taskdef load(df):    df.write.mode("overwrite").save_as_table("ANALYTICS.TRANSFORMED_DATA")@flow(name="full-snowflake-pipeline")def full_pipeline():    raw = extract()    staged = stage_to_snowflake(raw)    transformed = transform(staged)    load(transformed)
```

## Staging Conventions

Use internal stages for secure, fast ingestion.
Logical, predictable folder structure:

@my_stage/data/2026/01/01/


Store JSON, CSV, or Parquet as needed.


## Transform (Snowpark)
Patterns:

Schema enforcement via Snowpark DataFrames
Column derivations
UDF / Vectorized Python when required
Hybrid SQL + Snowpark when useful

## Tips

Use Snowpark for Python‑first teams.
Prefer SQL for set‑based logic.
Keep transformations deterministic and idempotent.


Loading – MERGE or Overwrite
Two standard options:
1) Overwrite (full rebuild)
Pythondf.write.mode("overwrite").save_as_table("DB.SCHEMA.TABLE")Show more lines
2) Incremental MERGE
Ideal for upserts and CDC‑style patterns.
SQLMERGE INTO target tUSING source sON t.id = s.idWHEN MATCHED THEN UPDATE SET ...WHEN NOT MATCHED THEN INSERT (...);Show more lines
Modeling tips

Separate staging, transform, and publish layers.
Use clustering on large analytic tables.


## CI/CD (optional examples)

CI: lint + format + tests
Snowflake deployments via Makefile or GitHub Actions
Optional Prefect deployments when flows/ changes


## Testing & Quality

Unit tests for session, loader, transformer modules
Data tests: schema + row count checks
Pre‑commit: flake8, black, pytest


## Operations

Observe via Prefect logs, Snowflake query history
Cost controls: warehouse size, auto‑suspend, clustering
Monitoring failures: Prefect alerts, Slack/SNS integrations


## Checklist Before Production

 Roles & least‑privilege permissions
 Warehouse auto‑suspend & sizing rules
 Proper stage cleanup strategy
 Error handling & retries in flows
 Clear staging → transform → publish layers
 Secret management (no hard‑coded passwords)
 CI pipelines passing


## License & Contributions
PA’s standard licensing — PRs welcome for additional patterns (MERGE helpers, dbt models, Streams/Tasks orchestration, external stage ingestion, etc.).
