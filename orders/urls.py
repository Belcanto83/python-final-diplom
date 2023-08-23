"""
URL configuration for orders project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter

from backend.views import index, UserViewSet, ShopView, ProductViewSet, BasketViewSet, CategoryViewSet, \
    RestoreUserPassword

router = DefaultRouter()
# router.register('shops', ShopViewSet, basename='shops')
router.register('users', UserViewSet, basename='users')
router.register('categories', CategoryViewSet, basename='categories')
router.register('products', ProductViewSet, basename='products')
router.register('basket', BasketViewSet, basename='basket')

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('api-token-auth/', views.obtain_auth_token),
    re_path(r'^api/v1/users/password_reset/(?P<token>[\w\d]+)/$', RestoreUserPassword.as_view(), name='password_reset'),
    path('api/v1/', include(router.urls)),
    path('api/v1/shops/', ShopView.as_view(), name='shop_create'),
    path('api/v1/shops/<int:pk>/', ShopView.as_view(), name='shop_update')
]
