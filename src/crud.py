import logging
from sqlalchemy.exc import IntegrityError
from src.database import AsyncSessionLocal
from src.models import Car

logger = logging.getLogger(__name__)


async def create_car(data: dict):
    """Save car in DB asynchronously"""
    async with AsyncSessionLocal() as db:
        try:
            car = Car(
                url=data['url'],
                title=data['title'],
                price_usd=data['price_usd'],
                odometer=data['odometer'],
                username=data['username'],
                phone_number=data['phone_number'],
                image_url=data['image_url'],
                images_count=data['images_count'],
                car_number=data['car_number'],
                car_vin=data['car_vin']
            )
            db.add(car)
            await db.commit()
            logger.info(f"Saved to DB: {data.get('title', 'Unknown')}")

        except IntegrityError:
            await db.rollback()
            logger.info(f"Duplicate skipped: {data['url']}")

        except Exception as e:
            await db.rollback()
            logger.error(f"DB Error: {e}")
