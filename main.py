import time
import schedule
import logging
import asyncio
import os
from tortoise import Tortoise

from src.scraper import run_scraper
from src.dumper import create_dump
from src.config import SCRAPE_TIME, TORTOISE_ORM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    logger.info("Initializing Tortoise ORM...")
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    logger.info("Database connected and schemas checked.")


async def close_db():
    await Tortoise.close_connections()


def run_scraper_job():
    """Обгортка для запуску скрапера"""
    logger.info("Starting scheduled scraper job...")
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def job_wrapper():
        await init_db()
        try:
            await run_scraper()
        finally:
            await close_db()

    try:
        asyncio.run(job_wrapper())
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)


def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def startup_check():
        await init_db()
        await close_db()

    asyncio.run(startup_check())

    logger.info(f"Scheduler started. Scraper set to run at {SCRAPE_TIME}")

    schedule.every().day.at(SCRAPE_TIME).do(run_scraper_job)
    schedule.every().day.at("23:55").do(create_dump)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Critical error in scheduler: {e}", exc_info=True)
        time.sleep(60)


if __name__ == "__main__":
    main()
