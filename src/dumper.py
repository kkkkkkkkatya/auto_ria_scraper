import subprocess
import os
import logging
from datetime import datetime
from src.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

def create_dump():
    """Creates an SQL dump of the database in the dumps/ folder."""
    dump_dir = "dumps"
    os.makedirs(dump_dir, exist_ok=True)

    filename = f"{dump_dir}/backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.sql"

    logger.info(f"Starting database dump to {filename}...")

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    command = [
        "pg_dump",
        "-h", DB_HOST,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-f", filename
    ]

    try:
        subprocess.run(command, env=env, check=True)
        logger.info("Database dump created successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating dump: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during dump: {e}")
