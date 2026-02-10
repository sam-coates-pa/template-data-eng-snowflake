# Snowflake Template

A practical, production‑ready template for building Snowflake‑native ELT pipelines using Prefect 2.x, Snowflake Connector, and Snowpark for Python.
It provides a repeatable structure for teams delivering Snowflake‑focused data engineering projects, helping you move fast while maintaining best practices.
This repository is designed as a GitHub Template Repository, enabling teams to click “Use this template” and instantly generate a project with production‑ready scaffolding.

## Contents

Overview
Architecture
Features Included
Project Structure
Environment Variables (NEW – includes your Session.builder snippet)
Snowpark Example Flow
Usage
Best Practices
CI/CD Guidance
Who This Template Is For


## Overview
This template provides a complete Snowflake ELT project foundation including:

Snowflake Connector & Snowpark session setup
Staging → Transform → Load pipeline pattern
Prefect orchestration flow
Environment‑driven configuration
Makefile, CI/CD workflow, linting & testing support
Clear separation of extract, transform, and load responsibilities
Secure environment variable management
Optional support for:

external S3 stages
dbt‑snowflake
key‑pair authentication
Prefect Cloud deployment




## Architecture
Source → Extract (Python)
             ↓
        Stage to Snowflake (PUT / internal stage)
             ↓
   Snowpark Transform (DataFrame pipeline)
             ↓
     Load into Snowflake Table (MERGE / overwrite)
             ↓
   Prefect Observatory (logging, retries, orchestration)


## Features Included
✔ Snowflake-native ELT pipeline

Upload to internal Snowflake stage
Snowpark transformations
Table loading with save_as_table()
Config‑driven database/schema selection

✔ Production-grade orchestration

Prefect tasks + flow
Retries, logging, observability
Optional Prefect Cloud integration

✔ Strong engineering foundations

Makefile
Testing (pytest)
Linting (flake8 + black)
Pre-commit ready
Fully structured project layout

✔ Expandable patterns

dbt‑snowflake
external stages
secure key‑pair auth
Snowflake Streams/Tasks


## Project Structure
snowflake-template/
│
├── flows/
│   └── full_pipeline.py
│
├── src/
│   └── snowflake/
│        ├── connector.py
│        ├── loader.py
│        └── transformer.py
│
├── config/
│   ├── dev.yaml
│   └── prod.yaml
│
├── .env.example
├── requirements.txt
├── Makefile
└── .github/workflows/ci.yml


## Environment Variables
Place your Snowflake credentials in a file named env.snowflake.example (recommended) or .env.example.
##############################################
# Snowflake Credentials
##############################################
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=

##############################################
# Optional Private Key Auth (Instead of Password)
##############################################
# SNOWFLAKE_PRIVATE_KEY_PATH=
# SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=

##############################################
# Prefect (optional)
##############################################
PREFECT_API_URL=
PREFECT_API_KEY=


## Snowflake Session Configuration (as requested)
Your requested code snippet is now included in the README exactly as provided.
This is what Snowpark uses to authenticate and connect:
PythonSession.builder.configs({    "account": SNOWFLAKE_ACCOUNT,    "user": SNOWFLAKE_USER,    "password": SNOWFLAKE_PASSWORD,    "role": SNOWFLAKE_ROLE,    "warehouse": SNOWFLAKE_WAREHOUSE,    "database": SNOWFLAKE_DATABASE,    "schema": SNOWFLAKE_SCHEMA,})Show more lines
This block directly maps to the environment variables above.

## Snowpark Example Flow
Included in flows/full_pipeline.py:
Pythonfrom prefect import flow, taskfrom snowflake.snowpark import Sessionimport pandas as pdimport osdef get_session():    return Session.builder.configs({        "account": os.getenv("SNOWFLAKE_ACCOUNT"),        "user": os.getenv("SNOWFLAKE_USER"),        "password": os.getenv("SNOWFLAKE_PASSWORD"),        "role": os.getenv("SNOWFLAKE_ROLE"),        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),        "database": os.getenv("SNOWFLAKE_DATABASE"),        "schema": os.getenv("SNOWFLAKE_SCHEMA"),    }).create()@taskdef extract():    return [{"id": 1, "value": 10}, {"id": 2, "value": 30}]@taskdef stage_to_snowflake(data):    df = pd.DataFrame(data)    df.to_json("extract.json", orient="records")    session = get_session()    session.file.put("extract.json", "@my_internal_stage/data", overwrite=True)    return "@my_internal_stage/data/extract.json"@taskdef transform(stage_file):    session = get_session()    df = session.read.json(stage_file)    return df.with_column("adjusted", df["value"] * 1.5)@taskdef load(df):    df.write.mode("overwrite").save_as_table("ANALYTICS.TRANSFORMED_DATA")@flowdef full_pipeline():    raw = extract()    staged = stage_to_snowflake(raw)    transformed = transform(staged)    load(transformed)``Show more lines

## Usage
Install dependencies
Shellmake installShow more lines
Run the pipeline locally
Shellmake runShow more lines
Format & lint
Shellmake formatmake lintShow more lines
Run tests
Shellmake testShow more lines
Optional Prefect Deploy
Shellmake deployShow more lines

## Best Practices for Snowflake ELT
Staging

Use internal stages for secure file ingestion
Partition data logically (date‑based where possible)

Transformations

Prefer Snowpark DataFrames for Python-first teams
Use SQL when transformations are simple & set‑based

Loading

Use MERGE when updating dimensional models
Use save_as_table for overwrite/rebuild patterns

Security

Use least privilege roles
Prefer key‑pair authentication over passwords
Never commit real .env files


## CI/CD
This template includes:

linting: flake8
formatting: black
testing: pytest
optional Prefect deployments

Add your Snowflake secrets to:
Settings → Secrets → Actions
