from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ProductInfo, Shop, Category, Product, User, Order, OrderItem


class ProductInfoInline(admin.TabularInline):
    model = ProductInfo


class ProductInline(admin.TabularInline):
    model = Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_id')
    inlines = [ProductInfoInline]


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'quantity', 'price', 'price_rrc', 'shop_id', 'article_nr')
    # list_filter = ('name', 'price', 'price_rrc')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'filename', 'user')
    inlines = [ProductInfoInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    inlines = [ProductInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'dt', 'user', 'delivery_address')
    list_filter = ('status',)
    inlines = [OrderItemInline]


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'company', 'position')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('id', 'username', 'first_name', 'last_name', 'email',
                    'company', 'position', 'phone', 'type')
