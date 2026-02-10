import logging
from tortoise.exceptions import IntegrityError
from src.models import Car

logger = logging.getLogger(__name__)


async def create_car(car_data: dict):
    """
    Зберігає авто в базу через Tortoise ORM.
    """
    try:
        exists = await Car.filter(url=car_data["url"]).exists()

        if exists:
            return None

        # 2. Створюємо нове авто
        new_car = await Car.create(
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
        return new_car

    except IntegrityError:
        logger.warning(f"Duplicate car ignored: {car_data['url']}")
        return None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None
