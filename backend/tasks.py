import yaml

from orders.celery import app

from .errors import IncorrectFileFormatError
from .mailings import test_1, send_order_confirmation_email, send_reset_pass_email, send_email
from .models import Category, Product, ProductInfo, Parameter, ProductParameter


@app.task
def test_task(task_id):
    res = test_1(task_id)
    return res


@app.task
def send_confirmation_email(order_id, to_user_list):
    send_order_confirmation_email(order_id, to_user_list)


@app.task
def send_reset_password_email(link, to_user_list):
    send_reset_pass_email(link, to_user_list)


@app.task
def import_goods(file_name, shop):
    try:
        with open(file_name, encoding='utf-8') as f:
            shop_products = yaml.load(f, Loader=yaml.FullLoader)
        # Проходим по очереди по всем категориям
        for category in shop_products['categories']:
            category_object, created = Category.objects.get_or_create(name=category['name'],
                                                                      defaults={'name': category['name']})
            category_object.shops.add(shop)
            # Создаём продукты определённой категории
            category_products = list(
                filter(lambda itm: itm['category'] == category['id'], shop_products['goods']))
            products = []
            for product in category_products:
                product_object, created = Product.objects.get_or_create(
                    name=product['name'],
                    category=category_object,
                    defaults={'name': product['name'], 'category': category_object}
                )
                products.append(product_object)
            # products = [Product(name=itm["name"], category=category_object) for itm in category_products]
            # products = Product.objects.bulk_create(products)
            product_infos = [ProductInfo(
                name=itm["name"],
                quantity=itm["quantity"],
                price=itm["price"],
                price_rrc=itm["price_rrc"],
                product=products[ind],
                shop=shop,
                article_nr=itm["id"]
            ) for ind, itm in enumerate(category_products)]
            product_infos = ProductInfo.objects.bulk_create(product_infos)
            # Создаём параметры для каждого продукта определённой категории
            for ind, product in enumerate(category_products):
                for key, value in product['parameters'].items():
                    parameter_object, created = Parameter.objects.get_or_create(name=key,
                                                                                defaults={'name': key})
                    product_parameter = ProductParameter(
                        value=value,
                        parameter=parameter_object,
                        product_info=product_infos[ind]
                    )
                    product_parameter.save()
        print('Goods are imported successfully!')
        send_email('Import goods', 'Goods are imported successfully!', [shop.user.email])
    except:
        print('Error: incorrect file format!')
        send_email('Import goods', 'Error: incorrect file format!', [shop.user.email])


@app.task
def update_goods(file_name, shop):
    try:
        with open(file_name, encoding='utf-8') as f:
            shop_products = yaml.load(f, Loader=yaml.FullLoader)
        # Проходим по очереди по всем категориям
        for category in shop_products['categories']:
            category_object, created = Category.objects.get_or_create(name=category['name'],
                                                                      defaults={'name': category['name']})
            # Создаём новую категорию товаров в данном магазине, только если её ещё нет!
            if created:
                category_object.shops.add(shop)
            # Обновляем(!) ИМЕЮЩИЕСЯ или создаём(!) НОВЫЕ продукты определённой категории
            category_products = list(
                filter(lambda itm: itm['category'] == category['id'], shop_products['goods']))
            for product in category_products:
                product_object, created = Product.objects.get_or_create(
                    name=product['name'],
                    category=category_object,
                    defaults={'name': product['name'], 'category': category_object}
                )
                product_info, created = ProductInfo.objects.update_or_create(shop=shop, product=product_object,
                                                                             defaults={'name': product['name'],
                                                                                       'quantity': product[
                                                                                           'quantity'],
                                                                                       'price': product[
                                                                                           'price'],
                                                                                       'price_rrc': product[
                                                                                           'price_rrc'],
                                                                                       'article_nr': product[
                                                                                           'id']})
                # Создаём параметры для каждого продукта определённой категории
                for key, value in product['parameters'].items():
                    parameter_object, created = Parameter.objects.get_or_create(name=key,
                                                                                defaults={'name': key})
                    ProductParameter.objects.update_or_create(parameter=parameter_object,
                                                              product_info=product_info,
                                                              defaults={'value': value})
        print('Goods are updated successfully!')
        send_email('Import goods', 'Goods are updated successfully!', [shop.user.email])
    except:
        print('Error: incorrect file format!')
        send_email('Import goods', 'Error: incorrect file format!', [shop.user.email])

    # TODO 02: Реализовать механизм удаления записей, на которые нет внешних ссылок из связанных таблиц
