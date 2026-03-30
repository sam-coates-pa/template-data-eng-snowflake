import os
import snowflake.connector
from connector import get_snowflake_connection


def stage_file(file_path: str, stage_name: str, env: str = "dev"):
    """
    Uploads a file to a Snowflake internal stage.
    Uses PUT <file> @stage syntax.
    """

    conn = get_snowflake_connection(env)
    cur = conn.cursor()

    try:
        # Snowflake expects paths like @database.schema.stage
        put_sql = f"PUT file://{file_path} {stage_name} AUTO_COMPRESS=TRUE"
        cur.execute(put_sql)

        return f"{stage_name}/{os.path.basename(file_path)}"
    finally:
        cur.close()
        conn.close()


def copy_into_table(table: str, stage_path: str, file_format: dict, env: str = "dev"):
    """
    Issues a COPY INTO <table> command from stage_path.
    file_format should match config["data_load"]["file_format"]
    """

    conn = get_snowflake_connection(env)
    cur = conn.cursor()

    try:
        fmt_type = file_format.get("type", "PARQUET")

        if fmt_type.upper() == "PARQUET":
            format_clause = "FILE_FORMAT = (TYPE = PARQUET)"
        elif fmt_type.upper() == "JSON":
            fmt_jsonpath = file_format.get("strip_outer_array", True)
            format_clause = f"FILE_FORMAT = (TYPE = JSON STRIP_OUTER_ARRAY = {str(fmt_jsonpath).upper()})"
        else:
            raise ValueError("Unsupported file format: " + fmt_type)

        sql = f"""
        COPY INTO {table}
        FROM '{stage_path}'
        {format_clause}
        PATTERN='.*'
        ON_ERROR='ABORT_STATEMENT';
        """

        cur.execute(sql)
        results = cur.fetchall()
        return results

    finally:
        cur.close()
        conn.close()


def validate_row_count(table: str, env: str = "dev") -> int:
    """Returns COUNT(*) from a Snowflake table."""

    conn = get_snowflake_connection(env)
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        (count,) = cur.fetchone()
        return count

    finally:
        cur.close()
        conn.close()
