import snowflake.connector
import yaml


def load_config(env: str = "dev"):
    """Load environment YAML from config folder."""
    with open(f"config/{env}.yaml", "r") as f:
        return yaml.safe_load(f)


def get_snowflake_connection(env: str = "dev"):
    """
    Creates and returns a Snowflake connector connection
    using parameters from config/<env>.yaml.
    """

    config = load_config(env)
    sf = config["snowflake"]

    conn = snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        role=sf["role"],
        warehouse=sf["warehouse"],
        database=sf["database"],
        schema=sf["schema"],
        authenticator=sf.get("authenticator", "snowflake"),
        private_key_path=sf.get("private_key_path"),
        password=sf.get("password"),
    )

    return conn
