import time
import schedule
import logging

from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from src.scraper import run_scraper
from src.dumper import create_dump
from src.database import engine
from src.models import Base
from src.config import SCRAPE_TIME


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def wait_for_db():
    logger.info("Waiting for database...")

    db_conn = None
    while not db_conn:
        try:
            db_conn = engine.connect()
            db_conn.execute(text("SELECT 1"))
            db_conn.close()
            logger.info("Database available!")
            return
        except OperationalError:
            logger.warning("Database unavailable, waiting 1 second...")
            time.sleep(1)

def init_db():
    """Створює таблиці, якщо їх немає."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")


def main():
    wait_for_db()
    init_db()

    logger.info(f"Scheduler started. Scraper set to run at {SCRAPE_TIME}")
    schedule.every().day.at(SCRAPE_TIME).do(run_scraper)
    schedule.every().day.at("23:55").do(create_dump)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Critical error in scheduler: {e}", exc_info=True)

        time.sleep(60)


if __name__ == "__main__":
    main()
