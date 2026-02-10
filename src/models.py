from tortoise import fields, models


class Car(models.Model):
    id = fields.IntField(pk=True)
    url = fields.CharField(max_length=255, unique=True)
    title = fields.CharField(max_length=255, null=True)
    price_usd = fields.IntField(null=True)
    odometer = fields.IntField(null=True)
    username = fields.CharField(max_length=255, null=True)
    phone_number = fields.BigIntField(null=True)
    image_url = fields.TextField(null=True)
    images_count = fields.IntField(null=True)

    car_number = fields.CharField(max_length=255, null=True)
    car_vin = fields.CharField(max_length=255, null=True)

    datetime_found = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "cars"

    def __str__(self):
        return f"<Car(id={self.id}, title='{self.title}', url={self.url})>"
