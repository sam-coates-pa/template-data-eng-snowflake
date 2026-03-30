import os
import yaml
from datetime import datetime
from prefect import flow, task, get_run_logger

# Local modules in your template repo
from connector import get_snowflake_connection
from transformer import transform_dataframe
from loader import stage_file, copy_into_table, validate_row_count


# ---------------------------------------------------------
# Load YAML configuration (dev or prod)
# ---------------------------------------------------------
def load_config(env: str):
    config_path = f"config/{env}.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------
# PREFECT TASKS
# ---------------------------------------------------------

@task
def extract_data(config):
    """
    Extract raw data from local example parquet for template repo.
    """
    logger = get_run_logger()
    logger.info("Extracting raw data from local parquet...")

    import pandas as pd

    df = pd.read_parquet(config["paths"]["local_data_path"])
    logger.info(f"Loaded {len(df)} rows from parquet.")

    return df


@task
def transform_data(df):
    """
    Uses your transformer.py logic.
    """
    logger = get_run_logger()
    logger.info("Transforming data using transformer.py...")

    transformed_df = transform_dataframe(df)
    logger.info(f"Transformed dataset has {len(transformed_df)} rows.")

    return transformed_df


@task
def stage_data(config, df):
    """
    Stages transformed data into Snowflake internal stage.
    """
    logger = get_run_logger()
    logger.info("Staging transformed data...")

    # Save as temp file for upload
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    temp_path = f"/tmp/transformed_{timestamp}.parquet"

    df.to_parquet(temp_path)
    logger.info(f"Temp parquet written to {temp_path}")

    stage_location = stage_file(
        file_path=temp_path,
        stage_name=config["paths"]["staging_directory"],
    )

    logger.info(f"File staged to {stage_location}")
    return stage_location


@task
def load_into_snowflake(config, staged_path):
    """
    Executes COPY INTO <table>
    """
    logger = get_run_logger()
    logger.info("Executing COPY INTO ...")

    result = copy_into_table(
        table=config["data_load"]["target_table"],
        stage_path=staged_path,
        file_format=config["data_load"]["file_format"],
    )

    logger.info(f"Loaded rows: {result}")
    return result


@task
def validate_loaded_data(config, expected_count):
    """
    Optional validation step from loader.py
    """
    logger = get_run_logger()
    logger.info("Validating row count inside Snowflake...")

    actual = validate_row_count(config["data_load"]["target_table"])

    logger.info(f"Expected: {expected_count}, Actual: {actual}")

    return {
        "expected": expected_count,
        "actual": actual,
        "match": expected_count == actual
    }


# ---------------------------------------------------------
# FULL PREFECT FLOW
# ---------------------------------------------------------

@flow(name="snowflake-full-pipeline")
def full_snowflake_pipeline(env: str = "dev"):
    logger = get_run_logger()
    logger.info(f"Running pipeline for environment: {env}")

    # Load YAML config (dev.yaml or prod.yaml)
    config = load_config(env)

    # Extract → Transform → Stage → Load → Validate
    df_raw = extract_data(config)
    df_transformed = transform_data(df_raw)

    staged_path = stage_data(config, df_transformed)

    load_result = load_into_snowflake(config, staged_path)

    validation = validate_loaded_data(config, len(df_transformed))

    logger.info("Pipeline complete.")
    logger.info(f"Validation: {validation}")

    return {
        "load_result": load_result,
        "validation": validation
    }


# ---------------------------------------------------------
# LOCAL EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    full_snowflake_pipeline(env=os.getenv("ENV", "dev"))
