import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database import AsyncSessionLocal
from src.models import Car

logger = logging.getLogger(__name__)


async def create_car(car_data: dict):
    """
    Зберігає авто в базу.
    КРИТИЧНО: Сесія створюється тут, локально, для кожного окремого авто.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                query = select(Car).where(Car.url == car_data["url"])
                result = await session.execute(query)
                existing_car = result.scalar_one_or_none()

                if existing_car:
                    return existing_car

                new_car = Car(
                    url=car_data["url"],
                    title=car_data["title"],
                    price_usd=car_data["price_usd"],
                    odometer=car_data["odometer"],
                    username=car_data["username"],
                    phone_number=car_data["phone_number"],
                    image_url=car_data["image_url"],
                    images_count=car_data["images_count"],
                    car_number=car_data["car_number"],
                    car_vin=car_data["car_vin"],
                )

                session.add(new_car)
                return new_car

            except IntegrityError:
                logger.warning(f"Duplicate car detected and ignored: {car_data['url']}")
                await session.rollback()
            except Exception as e:
                logger.error(f"Error saving car {car_data['url']}: {e}")
                await session.rollback()
                return None
