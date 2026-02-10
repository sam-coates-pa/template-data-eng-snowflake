
from prefect import flow, task
import snowflake.connector

@task
def extract():
    return {"sample": 123}

@task
def load_to_stage(data):
    return "@my_stage/path/file.json"

@task
def snowflake_transform():
    return True

@task
def snowflake_load():
    return True

@flow(name="snowflake-full-pipeline")
def pipeline():
    d = extract()
    load_to_stage(d)
    snowflake_transform()
    snowflake_load()

if __name__ == '__main__':
    pipeline()
