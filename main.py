import time
import schedule
import logging
import asyncio
import os

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


async def wait_for_db():
    """Асинхронна перевірка доступності БД."""
    logger.info("Waiting for database...")

    while True:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("Database available!")
            return
        except OperationalError:
            logger.warning("Database unavailable, waiting 1 second...")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Unknown DB error: {e}")
            await asyncio.sleep(1)


async def init_db():
    """Асинхронне створення таблиць."""
    logger.info("Initializing database...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized.")


def run_startup_tasks():
    # if os.name == 'nt':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def startup():
        await wait_for_db()
        await init_db()

    asyncio.run(startup())


def run_scraper_job():
    """Обгортка для запуску скрапера через schedule"""
    logger.info("Starting scheduled scraper job...")
    # if os.name == 'nt':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(run_scraper())
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)


def main():
    run_startup_tasks()

    logger.info(f"Scheduler started. Scraper set to run at {SCRAPE_TIME}")

    schedule.every().day.at(SCRAPE_TIME).do(run_scraper_job)
    schedule.every().day.at("23:55").do(create_dump)

    # (Опціонально) Запустити скрапер одразу для тесту, розкоментуй якщо треба:
    run_scraper_job()

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Critical error in scheduler: {e}", exc_info=True)

        time.sleep(60)


if __name__ == "__main__":
    main()
