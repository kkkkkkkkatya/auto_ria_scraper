from datetime import datetime

from sqlalchemy import Integer, String, BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True protects from duplicates
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    price_usd: Mapped[int | None] = mapped_column(Integer)
    odometer: Mapped[int | None] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[int | None] = mapped_column(BigInteger)
    image_url: Mapped[str | None] = mapped_column(String)
    images_count: Mapped[int | None] = mapped_column(Integer)
    car_number: Mapped[str | None] = mapped_column(String(255))
    car_vin: Mapped[str | None] = mapped_column(String(255))
    # func.now() automatically sets time
    datetime_found: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Car(id={self.id}, title='{self.title}', url={self.url})>"
