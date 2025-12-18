import logging
from sqlalchemy.exc import IntegrityError
from src.database import get_db
from src.models import Car


logger = logging.getLogger(__name__)


def create_car(data: dict):
    """Save car in DB"""
    db = next(get_db())
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
        db.commit()
        logger.info(f"Saved to DB: {data['title']}")
    except IntegrityError:
        db.rollback()
        logger.info(f"Duplicate skipped: {data['url']}")
    except Exception as e:
        db.rollback()
        logger.error(f"DB Error: {e}")
    finally:
        db.close()
