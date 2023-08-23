from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


def get_shop_directory(instance, filename):
    return f'{instance.id}/{filename}'


class UserTypeChoices(models.TextChoices):
    """Типы пользователя сервиса"""
    SHOP = "SHOP", "Магазин (поставщик)"
    BUYER = "BUYER", "Покупатель"


class OrderStatusChoices(models.TextChoices):
    """Возможные статусы заказа"""
    BASKET = "BASKET", "В корзине"
    # NEW = "NEW", "Новый"
    CONFIRMED = "CONFIRMED", "Подтверждён"
    ASSEMBLED = "ASSEMBLED", "Собран"
    SENT = "SENT", "Отправлен"
    DELIVERED = "DELIVERED", "Доставлен"
    CANCELED = "CANCELED", "Отменён"


class User(AbstractUser):
    company = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    phone = models.PositiveBigIntegerField()
    type = models.CharField(max_length=50, choices=UserTypeChoices.choices)
    # orders
    # shop
    REQUIRED_FIELDS = ['company', 'position', 'phone', 'type']


class RestorePasswordToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restore_pass_token')
    token = models.CharField(max_length=50, unique=True)


class Shop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField(null=True, blank=True)
    filename = models.FileField(upload_to=get_shop_directory, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop', null=True, blank=True)
    # categories
    # products

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        file_field = None
        if not self.pk:
            file_field = self.filename
            self.filename = None
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )
        if file_field:
            self.filename = file_field
            super().save(
                force_insert=False,
                force_update=True,
                using=using,
                update_fields=['filename']
            )


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    shops = models.ManyToManyField(Shop, related_name='categories')
    # products


# пока не используем, т.к. не задали атрибут "through" в свойстве "shops" выше
# class ShopCategory(models.Model):
#     shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='shop_categories')
#     category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_shops')


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    # shops


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='shops')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    quantity = models.PositiveSmallIntegerField()
    price = models.PositiveIntegerField()
    price_rrc = models.PositiveIntegerField()
    article_nr = models.PositiveIntegerField(null=True, blank=True)
    # parameters
    # order_items

    class Meta:
        constraints = [models.UniqueConstraint(fields=('product', 'shop'), name='unique_product_info'), ]


class Parameter(models.Model):
    name = models.CharField(max_length=100, unique=True)


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, related_name='parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('product_info', 'parameter'), name='unique_product_parameter'), ]


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    dt = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50,
                              choices=OrderStatusChoices.choices,
                              default=OrderStatusChoices.BASKET)
    delivery_address = models.CharField(max_length=100, null=True, blank=True)
    # order_items


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=('order', 'product_info'), name='unique_order_item'), ]
