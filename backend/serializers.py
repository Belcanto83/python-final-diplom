import os
import yaml
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from .errors import IncorrectFileFormatError
from .models import Shop, User, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, \
    UserTypeChoices
from .tasks import import_goods, update_goods


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'email', 'company', 'position', 'phone', 'type')

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            company=validated_data['company'],
            position=validated_data['position'],
            phone=validated_data['phone'],
            type=validated_data['type']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        update_fields = ['username', 'first_name', 'last_name', 'email', 'company', 'position', 'phone']
        for field in update_fields:
            value = validated_data.get(field, getattr(instance, field))
            setattr(instance, field, value)
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        return instance


class GeneralShopSerializer(ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name',)


class ShopSerializer(ModelSerializer):
    # получаем "user" из объекта "request" (через API перезаписать "user" нельзя!)
    # user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'filename', 'user_email')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        shop = super().create(validated_data)
        if validated_data.get('filename', None):
            f_name = os.path.join(settings.MEDIA_ROOT, str(shop.id), validated_data["filename"].name)
            import_goods.delay(f_name, shop)
            # try:
            #     with open(f_name, encoding='utf-8') as f:
            #         shop_products = yaml.load(f, Loader=yaml.FullLoader)
            #     # Проходим по очереди по всем категориям
            #     for category in shop_products['categories']:
            #         category_object, created = Category.objects.get_or_create(name=category['name'],
            #                                                                   defaults={'name': category['name']})
            #         category_object.shops.add(shop)
            #         # Создаём продукты определённой категории
            #         category_products = list(
            #             filter(lambda itm: itm['category'] == category['id'], shop_products['goods']))
            #         products = []
            #         for product in category_products:
            #             product_object, created = Product.objects.get_or_create(
            #                 name=product['name'],
            #                 category=category_object,
            #                 defaults={'name': product['name'], 'category': category_object}
            #             )
            #             products.append(product_object)
            #         # products = [Product(name=itm["name"], category=category_object) for itm in category_products]
            #         # products = Product.objects.bulk_create(products)
            #         product_infos = [ProductInfo(
            #             name=itm["name"],
            #             quantity=itm["quantity"],
            #             price=itm["price"],
            #             price_rrc=itm["price_rrc"],
            #             product=products[ind],
            #             shop=shop,
            #             article_nr=itm["id"]
            #         ) for ind, itm in enumerate(category_products)]
            #         product_infos = ProductInfo.objects.bulk_create(product_infos)
            #         # Создаём параметры для каждого продукта определённой категории
            #         for ind, product in enumerate(category_products):
            #             for key, value in product['parameters'].items():
            #                 parameter_object, created = Parameter.objects.get_or_create(name=key,
            #                                                                             defaults={'name': key})
            #                 product_parameter = ProductParameter(
            #                     value=value,
            #                     parameter=parameter_object,
            #                     product_info=product_infos[ind]
            #                 )
            #                 product_parameter.save()
            # except:
            #     raise IncorrectFileFormatError('File has incorrect format')
        return shop

    def update(self, instance, validated_data):
        validated_data['user'] = self.context['request'].user
        shop = super().update(instance, validated_data)
        if validated_data.get('filename', None):
            f_name = os.path.join(settings.MEDIA_ROOT, shop.filename.name)
            update_goods.delay(f_name, shop)
        #     try:
        #         with open(f_name, encoding='utf-8') as f:
        #             shop_products = yaml.load(f, Loader=yaml.FullLoader)
        #         # Проходим по очереди по всем категориям
        #         for category in shop_products['categories']:
        #             category_object, created = Category.objects.get_or_create(name=category['name'],
        #                                                                       defaults={'name': category['name']})
        #             # Создаём новую категорию товаров в данном магазине, только если её ещё нет!
        #             if created:
        #                 category_object.shops.add(shop)
        #             # Обновляем(!) ИМЕЮЩИЕСЯ или создаём(!) НОВЫЕ продукты определённой категории
        #             category_products = list(
        #                 filter(lambda itm: itm['category'] == category['id'], shop_products['goods']))
        #             for product in category_products:
        #                 product_object, created = Product.objects.get_or_create(
        #                     name=product['name'],
        #                     category=category_object,
        #                     defaults={'name': product['name'], 'category': category_object}
        #                 )
        #                 product_info, created = ProductInfo.objects.update_or_create(shop=shop, product=product_object,
        #                                                                              defaults={'name': product['name'],
        #                                                                                        'quantity': product[
        #                                                                                            'quantity'],
        #                                                                                        'price': product[
        #                                                                                            'price'],
        #                                                                                        'price_rrc': product[
        #                                                                                            'price_rrc'],
        #                                                                                        'article_nr': product[
        #                                                                                            'id']})
        #                 # Создаём параметры для каждого продукта определённой категории
        #                 for key, value in product['parameters'].items():
        #                     parameter_object, created = Parameter.objects.get_or_create(name=key,
        #                                                                                 defaults={'name': key})
        #                     ProductParameter.objects.update_or_create(parameter=parameter_object,
        #                                                               product_info=product_info,
        #                                                               defaults={'value': value})
        #     except:
        #         raise IncorrectFileFormatError('File has incorrect format')
        # # TODO 01: Реализовать механизм удаления записей, на которые нет внешних ссылок из связанных таблиц
        return shop


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)


class ProductInfoSerializer(ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'price_rrc', 'article_nr', 'shop_name')


class OrderItemSerializer(ModelSerializer):
    product_name = serializers.CharField(source='product_info.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('quantity', 'product_name', 'product_info')


class BasketSerializer(ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    order_items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'user_email', 'order_items')

    def create(self, validated_data):
        order_items = validated_data.pop('order_items', [])
        validated_data['user'] = self.context['request'].user
        order = super().create(validated_data)
        order_items = [OrderItem(order=order, **itm) for itm in order_items]
        OrderItem.objects.bulk_create(order_items)
        return order

    def update(self, instance, validated_data):
        request_items = validated_data.pop('order_items', [])
        order = super().update(instance, validated_data)
        # Находим в базе уже СУЩЕСТВУЮЩИЕ продукты, которые нужно обновить
        # 1. Находим в базе ВСЕ продукты, которые относятся к текущему заказу (корзине)
        database_products = list(instance.order_items.filter(order=order))
        # 2. Формируем 3 множества элементов (продуктов): to_update_in_db, to_add_to_db, to_delete_from_db
        i = 0
        db_products_to_update = []
        request_items_to_update = []
        while i < len(database_products):
            database_product = database_products[i]
            for request_item in request_items:
                if database_product.product_info_id == request_item['product_info'].id:
                    db_products_to_update.append(database_product)
                    request_items_to_update.append(request_item)
                    database_products.remove(database_product)
                    request_items.remove(request_item)
                    break
            else:
                i += 1
        # 3. Обновляем уже ИМЕЮЩИЕСЯ продукты в базе
        for db_product, request_itm in zip(db_products_to_update, request_items_to_update):
            db_product.quantity = request_itm.get('quantity', db_product.quantity)
        OrderItem.objects.bulk_update(objs=db_products_to_update, fields=['quantity'])
        # 4. Добавляем новые продукты в базу
        db_products_to_create = [OrderItem(order=order, **itm) for itm in request_items]
        OrderItem.objects.bulk_create(db_products_to_create)
        # 5. Удаляем ненужные продукты из базы
        db_products_to_delete = [itm.product_info_id for itm in database_products]
        OrderItem.objects.filter(product_info_id__in=db_products_to_delete, order=order).delete()
        return order

    def validate(self, attrs):
        if self.context['request'].user.type != UserTypeChoices.BUYER:
            raise ValidationError('Only for buyers, not for shops')
        return attrs
