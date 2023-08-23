import django_filters

from backend.models import ProductInfo


class ProductInfoFilter(django_filters.FilterSet):
    price_rrc = django_filters.RangeFilter()
    category = django_filters.CharFilter(field_name='product__category__name', lookup_expr='icontains')

    class Meta:
        model = ProductInfo
        fields = ['name', 'price_rrc', 'article_nr', 'category']
