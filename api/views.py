# api/views.py
from decimal import Decimal
from rest_framework import viewsets, generics, status, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
from django.http import JsonResponse
from rest_framework.decorators import api_view, action
from django.db.models import Q, Min, Max, Count
from .models import Brand, Product
from .serializers import BrandSerializer, ProductListSerializer
from .filters import BrandFilter

from .pagination import StandardResultsSetPagination
from .models import (
    Category, Product, NewsItem, AboutContent,
    ContactInfo, ContactMessage, Brand, ProductFeature, Tag, Feature, ProductTagGroup, TagName, FeatureValue, Image
)
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    NewsItemSerializer, NewsDetailSerializer, AboutContentSerializer,
    ContactInfoSerializer, ContactMessageSerializer, BrandSerializer, TagSerializer,
    ProductTagGroupSerializer
)
@api_view(['GET'])
def features_tags_by_category(request):
    category_id = request.GET.get('category')
    features = Feature.objects.filter(category_id=category_id)
    tags = Tag.objects.filter(category_id=category_id)
    tag_names = TagName.objects.filter(category_id=category_id)
    feature_values = FeatureValue.objects.filter(category_id=category_id)
    features_data = list(features.values('id', 'name'))
    tags_data = list(tags.values('id', 'name'))
    tag_names_data = list(tag_names.values('id', 'name'))
    feature_values_data = list(feature_values.values('id', 'value', 'feature_id', 'feature__name'))
    return JsonResponse({
        'features': features_data,
        'tags': tags_data,
        'tag_names': tag_names_data,
        'feature_values': feature_values_data
    })
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer

    @action(detail=False, methods=['get'])
    def with_count(self, request):
        tags = Tag.objects.annotate(count=Count('producttaggroup')).order_by('-count')
        data = [{'id': t.id, 'name': t.name, 'slug': t.slug, 'count': t.count} for t in tags]
        return Response(data)
    @api_view(['GET'])
    def features_tags_by_category(request):
        category_id = request.GET.get('category')
        features = Feature.objects.filter(category_id=category_id)
        tags = Tag.objects.filter(category_id=category_id)
        features_data = list(features.values('id', 'name'))
        tags_data = list(tags.values('id', 'name'))
        return JsonResponse({
            'features': features_data,
            'tags': tags_data
        })
        return JsonResponse({'tags': tags_data})

@api_view(['GET'])
def products_by_feature_value(request):
    value = request.GET.get('value')
    if not value:
        return Response({"error": "value parameter is required"}, status=400)

    product_ids = ProductFeature.objects.filter(value__icontains=value).values_list('product_id', flat=True)
    queryset = Product.objects.filter(id__in=product_ids).distinct()

    serializer = ProductListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


def apply_product_filters(request, queryset):
    params = request.query_params
    tag_param = params.get('tag')  # сюда приходит slug или имя
    if tag_param:
        tag_slugs = [t.strip() for t in tag_param.split(',') if t.strip()]
        queryset = queryset.filter(
            Q(tag_groups__tags__slug__in=tag_slugs) |
            Q(tag_groups__tags__name__in=tag_slugs)
        )

    # --- фильтр по цене ---
    price_min = params.get('price_min')
    price_max = params.get('price_max')
    if price_min:
        try:
            queryset = queryset.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            queryset = queryset.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # --- фильтр по бренду ---
    brand_param = params.get('brand')
    if brand_param:
        slugs = [s.strip() for s in brand_param.split(',') if s.strip()]
        queryset = queryset.filter(brand__slug__in=slugs)

    # --- фильтр доступности ---
    is_av = params.get('is_available')
    if is_av is not None:
        val = str(is_av).lower()
        if val in ('true', '1', 'yes'):
            queryset = queryset.filter(is_available=True)
        elif val in ('false', '0', 'no'):
            queryset = queryset.filter(is_available=False)


    # --- фильтр по поиску ---
    search = params.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # --- фильтр по характеристикам ---
    for k, v in params.items():
        if k.startswith('feature_') and v:
            try:
                fid = int(k.split('_', 1)[1])
                queryset = queryset.filter(features__feature_id=fid, features__value__icontains=v)
            except (ValueError, IndexError):
                continue

    # --- фильтр по категории с рекурсией ---
    category_slug = params.get('category')
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)

            def collect_category_ids(cat):
                ids = [cat.id]
                for child in cat.children.all():
                    ids.extend(collect_category_ids(child))
                return ids

            category_ids = collect_category_ids(category)
            queryset = queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            queryset = queryset.none()
    # --- фильтр по группам тегов ---
    for key, val in params.items():
        if key.startswith('taggroup_') and val:
            queryset = queryset.filter(tags__group__slug=key.split('_', 1)[1], tags__slug=val)

    # --- сортировка ---
    ordering = params.get('ordering', '-created_at')
    allowed = {'name', '-name', 'price', '-price', 'created_at', '-created_at'}
    if ordering not in allowed:
        ordering = '-created_at'
    queryset = queryset.order_by(ordering)

    return queryset.distinct()


# -------------------------
# ViewSets
# -------------------------



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Product.objects.all()
        # Don't apply filters for admin operations
        if self.action not in ['create', 'update', 'partial_update', 'destroy']:
            queryset = apply_product_filters(self.request, queryset)
        return queryset

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=False, methods=['get'], url_path='price-range')
    def price_range(self, request, *args, **kwargs):
        category_slug = request.query_params.get('category')

        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                qs = category.get_all_products().exclude(price__isnull=True)
            except Category.DoesNotExist:
                return Response({'min_price': None, 'max_price': None})
        else:
            qs = Product.objects.exclude(price__isnull=True)

        agg = qs.aggregate(min_price=Min('price'), max_price=Max('price'))

        return Response({
            'min_price': float(agg['min_price']) if agg['min_price'] else None,
            'max_price': float(agg['max_price']) if agg['max_price'] else None,
        })

    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, slug=None):
        """Upload multiple images for a product"""
        from .models import Image
        
        product = self.get_object()
        uploaded_images = []
        
        files = request.FILES.getlist('images')
        if not files:
            return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        for file in files:
            image = Image.objects.create(product=product, image=file)
            uploaded_images.append({'id': image.id, 'image': image.image.url})
        
        return Response({'images': uploaded_images}, status=status.HTTP_201_CREATED)


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, BrandFilter]
    search_fields = ['name', 'description']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Brand.objects.annotate(
            products_count=Count('products')
        )
        return queryset

    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, slug=None):
        brand = self.get_object()
        # Start from products belonging to this brand and apply the same product filters
        products_qs = Product.objects.filter(brand=brand)
        # Reuse global product filters (price, tags, category, search, availability, etc.)
        try:
            products_qs = apply_product_filters(request, products_qs)
        except Exception:
            # Fallback to a basic queryset if filtering fails for any reason
            products_qs = products_qs.order_by('name')

        page = self.paginate_queryset(products_qs)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(products_qs, many=True, context={"request": request})
        return Response(serializer.data)
        
    @action(detail=True, methods=['get'])
    def categories(self, request, slug=None):
        """Получить список категорий, в которых есть товары данного бренда"""
        brand = self.get_object()
        categories = Category.objects.filter(products__brand=brand).distinct()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tags(self, request, slug=None):
        """Получить список тегов, которые используются в товарах данного бренда"""
        brand = self.get_object()
        # Get ProductTagGroups for this brand's products
        products = Product.objects.filter(brand=brand)
        tag_groups = ProductTagGroup.objects.filter(
            product__in=products
        ).prefetch_related('tags').distinct()
        
        grouped_data = {}
        
        for group in tag_groups:
            tag_name_obj = group.group_name
            if not tag_name_obj:
                continue
            
            key = tag_name_obj.id
            if key not in grouped_data:
                grouped_data[key] = {
                    'id': tag_name_obj.id,
                    'group_name': tag_name_obj.name,
                    'tags': {}
                }
            
            for tag in group.tags.all():
                grouped_data[key]['tags'][tag.id] = {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug
                }
        
        result = [
            {
                'id': data['id'],
                'group_name': data['group_name'],
                'tags': list(data['tags'].values())
            }
            for data in grouped_data.values()
        ]
        
        return Response(result)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(parent=None).order_by('order', 'name')
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except (ValueError, TypeError):
                pass
        return queryset

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        try:
            category = self.get_object()
        except Http404:
            return Response({'error': 'Категория не найдена'}, status=404)

        products = category.get_all_products()
        products = apply_product_filters(request, products)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def brands(self, request, slug=None):
        try:
            category = self.get_object()
        except Http404:
            return Response({'error': 'Категория не найдена'}, status=404)
        products = category.get_all_products()
        brands = Brand.objects.filter(products__in=products).distinct()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tags(self, request, slug=None):
        try:
            category = self.get_object()
        except Http404:
            return Response({'error': 'Категория не найдена'}, status=404)
        
        products = category.get_all_products()
        tag_groups = ProductTagGroup.objects.filter(
            product__in=products
        ).prefetch_related('tags').distinct()
        
        grouped_data = {}
        
        for group in tag_groups:
            tag_name_obj = group.group_name
            if not tag_name_obj:
                continue
            
            # Use TagName id as key, extract name for display
            key = tag_name_obj.id
            if key not in grouped_data:
                grouped_data[key] = {
                    'id': tag_name_obj.id,
                    'group_name': tag_name_obj.name,
                    'tags': {}
                }
            
            for tag in group.tags.all():
                grouped_data[key]['tags'][tag.id] = {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug
                }
        
        result = [
            {
                'id': data['id'],
                'group_name': data['group_name'],
                'tags': list(data['tags'].values())
            }
            for data in grouped_data.values()
        ]
        
        return Response(result)


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsItem.objects.filter(is_published=True).order_by('-pub_date')
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NewsDetailSerializer
        return NewsItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except (ValueError, TypeError):
                pass
        return queryset


class AboutContentView(generics.RetrieveAPIView):
    serializer_class = AboutContentSerializer

    def get_object(self):
        obj = AboutContent.objects.first()
        if obj is None:
            return AboutContent(title='О нас', content='Информация временно отсутствует')
        return obj


class ContactInfoView(generics.RetrieveAPIView):
    serializer_class = ContactInfoSerializer

    def get_object(self):
        obj = ContactInfo.objects.first()
        if obj is None:
            return ContactInfo(phone='', email='', address='Информация отсутствует')
        return obj


class ContactMessageView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response({'message': 'Ваше сообщение успешно отправлено!'}, status=status.HTTP_201_CREATED)

# ============ ADMIN VIEWSETS ============
from .serializers import (
    CategoryAdminSerializer, ProductAdminSerializer, BrandAdminSerializer, TagAdminSerializer,
    TagNameAdminSerializer, FeatureAdminSerializer, FeatureValueAdminSerializer,
    NewsAdminSerializer, AboutContentAdminSerializer, ContactInfoAdminSerializer,
    ContactMessageAdminSerializer, ImageAdminSerializer,
    UserSerializer, LoginSerializer, ChangePasswordSerializer, UpdateProfileSerializer
)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class ProductAdminViewSet(viewsets.ModelViewSet):
    """CRUD для товаров (админка) с поддержкой inline изображений, характеристик и групп тегов"""
    queryset = Product.objects.all().select_related('category', 'brand').order_by('-created_at')
    serializer_class = ProductAdminSerializer
    lookup_field = 'pk'
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        brand = self.request.query_params.get('brand')
        is_available = self.request.query_params.get('is_available')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(internal_sku__icontains=search) | 
                Q(manufacturer_sku__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if brand:
            queryset = queryset.filter(brand_id=brand)
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() in ['true', '1'])
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Создание товара с inline данными"""
        data = request.data
        
        # Основные данные товара
        product_data = {
            'name': data.get('name'),
            'slug': data.get('slug') or None,
            'description': data.get('description', ''),
            'category_id': data.get('category'),
            'brand_id': data.get('brand') or None,
            'price': data.get('price') or None,
            'is_available': data.get('is_available', True),
            'manufacturer_sku': data.get('manufacturer_sku', ''),
            'internal_sku': data.get('internal_sku') or None,
        }
        
        product = Product(**product_data)
        product.save()
        
        # Обработка характеристик (features)
        features_data = data.get('features', [])
        for feat in features_data:
            if feat.get('feature_id') and feat.get('value_id'):
                ProductFeature.objects.create(
                    product=product,
                    feature_id=feat['feature_id'],
                    value_id=feat['value_id']
                )
        
        # Обработка групп тегов (tag_groups)
        tag_groups_data = data.get('tag_groups', [])
        for tg in tag_groups_data:
            if tg.get('group_name_id'):
                tag_group = ProductTagGroup.objects.create(
                    product=product,
                    group_name_id=tg['group_name_id']
                )
                tag_ids = tg.get('tag_ids', [])
                if tag_ids:
                    tag_group.tags.set(tag_ids)
        
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Обновление товара с inline данными"""
        partial = kwargs.pop('partial', False)
        product = self.get_object()
        data = request.data
        
        # Обновляем основные поля товара
        product.name = data.get('name', product.name)
        if 'slug' in data:
            product.slug = data['slug'] or product.slug
        product.description = data.get('description', product.description)
        if 'category' in data:
            product.category_id = data['category']
        if 'brand' in data:
            product.brand_id = data['brand'] or None
        if 'price' in data:
            product.price = data['price'] or None
        if 'is_available' in data:
            product.is_available = data['is_available']
        if 'manufacturer_sku' in data:
            product.manufacturer_sku = data['manufacturer_sku'] or ''
        if 'internal_sku' in data and data['internal_sku']:
            product.internal_sku = data['internal_sku']
        product.save()
        
        # Обновляем характеристики
        if 'features' in data:
            # Удаляем старые
            product.features.all().delete()
            # Создаем новые
            for feat in data['features']:
                if feat.get('feature_id') and feat.get('value_id'):
                    ProductFeature.objects.create(
                        product=product,
                        feature_id=feat['feature_id'],
                        value_id=feat['value_id']
                    )
        
        # Обновляем группы тегов
        if 'tag_groups' in data:
            # Удаляем старые
            product.tag_groups.all().delete()
            # Создаем новые
            for tg in data['tag_groups']:
                if tg.get('group_name_id'):
                    tag_group = ProductTagGroup.objects.create(
                        product=product,
                        group_name_id=tg['group_name_id']
                    )
                    tag_ids = tg.get('tag_ids', [])
                    if tag_ids:
                        tag_group.tags.set(tag_ids)
        
        # Обновляем изображения (порядок и is_main)
        if 'images' in data:
            for img_data in data['images']:
                if img_data.get('id'):
                    try:
                        img = Image.objects.get(id=img_data['id'], product=product)
                        if 'is_main' in img_data:
                            img.is_main = img_data['is_main']
                        if 'order' in img_data:
                            img.order = img_data['order']
                        if img_data.get('_delete'):
                            img.delete()
                        else:
                            img.save()
                    except Image.DoesNotExist:
                        pass
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        product = self.get_object()
        files = request.FILES.getlist('images')
        if not files:
            file = request.FILES.get('image')
            if file:
                files = [file]
        
        if not files:
            return Response({'error': 'No images provided'}, status=400)
        
        uploaded = []
        for f in files:
            img = Image.objects.create(product=product, image=f)
            uploaded.append({'id': img.id, 'image': img.image.url if img.image else None})
        
        return Response({'images': uploaded}, status=201)
    
    @action(detail=True, methods=['delete'], url_path='delete-image/(?P<image_id>[0-9]+)')
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        try:
            img = Image.objects.get(id=image_id, product=product)
            img.delete()
            return Response({'success': True})
        except Image.DoesNotExist:
            return Response({'error': 'Image not found'}, status=404)


class CategoryAdminViewSet(viewsets.ModelViewSet):
    """CRUD для категорий (админка)"""
    queryset = Category.objects.all().order_by('order', 'name')
    serializer_class = CategoryAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        parent = self.request.query_params.get('parent')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if parent:
            if parent == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent)
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        category = self.get_object()
        image = request.FILES.get('image')
        if image:
            category.image = image
            category.save()
            return Response({'image': category.image.url if category.image else None})
        return Response({'error': 'No image provided'}, status=400)


class BrandAdminViewSet(viewsets.ModelViewSet):
    """CRUD для брендов (админка)"""
    queryset = Brand.objects.all().order_by('name')
    serializer_class = BrandAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset
    
    @action(detail=True, methods=['post'], url_path='upload-logo')
    def upload_logo(self, request, pk=None):
        brand = self.get_object()
        logo = request.FILES.get('logo')
        if logo:
            brand.logo = logo
            brand.save()
            return Response({'logo': brand.logo.url if brand.logo else None})
        return Response({'error': 'No logo provided'}, status=400)


class TagAdminViewSet(viewsets.ModelViewSet):
    """CRUD для тегов (админка)"""
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset


class TagNameAdminViewSet(viewsets.ModelViewSet):
    """CRUD для имен тегов (админка)"""
    queryset = TagName.objects.all().order_by('name')
    serializer_class = TagNameAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset


class FeatureAdminViewSet(viewsets.ModelViewSet):
    """CRUD для характеристик (админка)"""
    queryset = Feature.objects.all().order_by('name')
    serializer_class = FeatureAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset


class FeatureValueAdminViewSet(viewsets.ModelViewSet):
    """CRUD для значений характеристик (админка)"""
    queryset = FeatureValue.objects.all().order_by('value')
    serializer_class = FeatureValueAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        
        if search:
            queryset = queryset.filter(value__icontains=search)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset


class NewsAdminViewSet(viewsets.ModelViewSet):
    """CRUD для новостей (админка)"""
    queryset = NewsItem.objects.all().order_by('-pub_date')
    serializer_class = NewsAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        is_published = self.request.query_params.get('is_published')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')
        
        return queryset


class ImageAdminViewSet(viewsets.ModelViewSet):
    """CRUD для изображений товаров (админка)"""
    queryset = Image.objects.all().order_by('order')
    serializer_class = ImageAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        return queryset


class AboutContentAdminView(generics.RetrieveUpdateAPIView):
    """Получение и обновление страницы О нас"""
    serializer_class = AboutContentAdminSerializer
    
    def get_object(self):
        obj = AboutContent.objects.first()
        if not obj:
            obj = AboutContent.objects.create(title='О нас', content='')
        return obj


class ContactInfoAdminView(generics.RetrieveUpdateAPIView):
    """Получение и обновление контактной информации"""
    serializer_class = ContactInfoAdminSerializer
    
    def get_object(self):
        obj = ContactInfo.objects.first()
        if not obj:
            obj = ContactInfo.objects.create(phone='', email='', address='')
        return obj


class ContactMessageAdminViewSet(viewsets.ModelViewSet):
    """Управление сообщениями от посетителей"""
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageAdminSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_processed = self.request.query_params.get('is_processed')
        
        if is_processed is not None:
            queryset = queryset.filter(is_processed=is_processed.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='mark-processed')
    def mark_processed(self, request, pk=None):
        message = self.get_object()
        message.is_processed = True
        message.save()
        return Response({'status': 'processed', 'id': message.id})
    
    @action(detail=True, methods=['post'], url_path='mark-unprocessed')
    def mark_unprocessed(self, request, pk=None):
        message = self.get_object()
        message.is_processed = False
        message.save()
        return Response({'status': 'unprocessed', 'id': message.id})


# ============ AUTH VIEWS ============

@api_view(['POST'])
def admin_login(request):
    """Вход в админку"""
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if user.is_staff or user.is_superuser:
            login(request, user)
            return Response({
                'message': 'Успешный вход',
                'user': UserSerializer(user).data
            })
        else:
            return Response({'error': 'Доступ запрещен. Требуются права администратора.'}, 
                          status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'Неверный логин или пароль'}, 
                       status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def admin_logout(request):
    """Выход из админки"""
    logout(request)
    return Response({'message': 'Вы вышли из системы'})


@api_view(['GET'])
def admin_me(request):
    """Получить текущего пользователя"""
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data)
    return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def admin_change_password(request):
    """Смена пароля"""
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response({'error': 'Неверный текущий пароль'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    # Перелогиниваем пользователя
    login(request, user)
    
    return Response({'message': 'Пароль успешно изменен'})


@api_view(['PUT', 'PATCH'])
def admin_update_profile(request):
    """Обновление профиля"""
    if not request.user.is_authenticated:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============ DASHBOARD STATS ============

@api_view(['GET'])
def admin_stats(request):
    """Статистика для Dashboard"""
    stats = {
        'products_count': Product.objects.count(),
        'categories_count': Category.objects.count(),
        'brands_count': Brand.objects.count(),
        'news_count': NewsItem.objects.count(),
        'published_news_count': NewsItem.objects.filter(is_published=True).count(),
        'unread_messages': ContactMessage.objects.filter(is_processed=False).count(),
        'total_messages': ContactMessage.objects.count(),
        'available_products': Product.objects.filter(is_available=True).count(),
        'tags_count': Tag.objects.count(),
        'features_count': Feature.objects.count(),
    }
    return Response(stats)