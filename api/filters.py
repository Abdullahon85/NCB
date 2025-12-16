# filters.py
import django_filters
from django.db.models import Q
from rest_framework import filters
from .models import Product, Brand

class ProductFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr='exact')
    
    class Meta:
        model = Product
        fields = ['price_min', 'price_max', 'category']

class BrandFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # Поиск по имени и описанию
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        # Фильтр по категориям через связанные продукты
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(products__category__slug=category).distinct()

        # Фильтр по наличию товаров
        has_products = request.query_params.get('has_products')
        if has_products:
            queryset = queryset.filter(products__isnull=False).distinct()

        # Фильтр по диапазону цен в продуктах
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')

        if price_min is not None:
            queryset = queryset.filter(products__price__gte=price_min).distinct()
        if price_max is not None:
            queryset = queryset.filter(products__price__lte=price_max).distinct()

        # Фильтр по наличию продуктов (is_available)
        has_available = request.query_params.get('has_available')
        if has_available:
            queryset = queryset.filter(products__is_available=True).distinct()

        # Сортировка
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering:
            if ordering == 'name':
                queryset = queryset.order_by('name')
            elif ordering == '-name':
                queryset = queryset.order_by('-name')
            elif ordering == '-products_count':
                queryset = queryset.annotate(
                    products_count=models.Count('products')
                ).order_by('-products_count')
            elif ordering == 'products_count':
                queryset = queryset.annotate(
                    products_count=models.Count('products')
                ).order_by('products_count')

        return queryset