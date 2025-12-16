# api/serializers.py
from rest_framework import serializers
from .models import (
    Category, Product, Image, Feature, ProductFeature, FeatureValue,
    NewsItem, AboutContent, ContactInfo, ContactMessage, Brand,
    Tag, ProductTagGroup, TagName
)
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class ProductTagGroupSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = ProductTagGroup
        fields = ['id', 'group_name', 'tags']

class PriceRangeSerializer(serializers.Serializer):
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'is_main', 'order']

class ProductFeatureSerializer(serializers.ModelSerializer):
    feature_name = serializers.CharField(source='feature.name', read_only=True, required=False)
    feature_id = serializers.PrimaryKeyRelatedField(
        source='feature',
        queryset=Feature.objects.all(),
        required=False,
        allow_null=True
    )
    value_id = serializers.PrimaryKeyRelatedField(
        source='value',
        queryset=FeatureValue.objects.all(),
        required=False,
        allow_null=True
    )
    value_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductFeature
        fields = ['id', 'feature_name', 'feature_id', 'value_id', 'value_name']

    def get_value_name(self, obj):
        """Safely get the value text from the FeatureValue object"""
        if obj.value:
            return obj.value.value
        return None

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent', 'children', 'products_count']
    
    def get_children(self, obj):
        children = obj.children.all().order_by('order', 'name')
        return CategorySerializer(children, many=True, context=self.context).data
    
    def get_products_count(self, obj):
        return obj.get_all_products().count()

class ProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', read_only=True)
    features = ProductFeatureSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'is_available',
            'main_image', 'category', 'category_id', 'manufacturer_sku', 'internal_sku', 'features', 'tags',
            'created_at', 'updated_at'
        ]

    def get_main_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return ImageSerializer(main_image).data
        first_image = obj.images.first()
        if first_image:
            return ImageSerializer(first_image).data
        return None

class BrandSerializer(serializers.ModelSerializer):
    # expose `image` property (frontend expects `image`) while the model field is `logo`
    image = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'image', 'description']

    def get_image(self, obj):
        if obj.logo:
            try:
                return obj.logo.url
            except Exception:
                return str(obj.logo)
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    features = ProductFeatureSerializer(many=True, required=False)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(write_only=True, source='category', queryset=Category.objects.all(), required=True)
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(write_only=True, source='brand', queryset=Brand.objects.all(), required=False, allow_null=True)
    tag_groups = ProductTagGroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'brand', 'brand_id', 'name', 'slug', 'description', 'price',
            'is_available', 'category', 'category_id', 'images', 'features',
            'manufacturer_sku', 'internal_sku', 'tag_groups', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        features_data = validated_data.pop('features', [])
        product = super().create(validated_data)
        # Create ProductFeature instances
        self._save_features(product, features_data)
        return product

    def update(self, instance, validated_data):
        features_data = validated_data.pop('features', None)
        product = super().update(instance, validated_data)
        # Update ProductFeature instances
        if features_data is not None:
            instance.features.all().delete()
            self._save_features(product, features_data)
        return product

    def _save_features(self, product, features_data):
        """Save ProductFeature instances for the product"""
        for feature_data in features_data:
            feature = feature_data.get('feature')
            value = feature_data.get('value')
            if feature and value:
                ProductFeature.objects.create(
                    product=product,
                    feature=feature,
                    value=value
                )

class NewsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = ['id', 'title', 'slug', 'preview', 'image', 'pub_date']

class NewsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = ['id', 'title', 'slug', 'content', 'preview', 'image', 'pub_date']

class AboutContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutContent
        fields = ['title', 'content', 'image']

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['phone', 'email', 'address', 'map_url']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']


# ============ ADMIN SERIALIZERS ============

class CategoryAdminSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'parent_name', 'image', 'order', 'products_count']
    
    def get_products_count(self, obj):
        return obj.products.count()


class ProductAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    images_count = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    # Inline данные для редактирования
    images = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    tag_groups = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'category', 'category_name',
            'brand', 'brand_name', 'is_available', 'manufacturer_sku', 'internal_sku',
            'created_at', 'images_count', 'main_image', 'images', 'features', 'tag_groups'
        ]
    
    def get_images_count(self, obj):
        return obj.images.count()
    
    def get_main_image(self, obj):
        main = obj.images.filter(is_main=True).first()
        if not main:
            main = obj.images.first()
        if main and main.image:
            try:
                return main.image.url
            except:
                return str(main.image)
        return None
    
    def get_images(self, obj):
        return [{
            'id': img.id,
            'image': img.image.url if img.image else None,
            'is_main': img.is_main,
            'order': img.order
        } for img in obj.images.all().order_by('order')]
    
    def get_features(self, obj):
        return [{
            'id': pf.id,
            'feature_id': pf.feature_id,
            'feature_name': pf.feature.name if pf.feature else None,
            'value_id': pf.value_id,
            'value_text': pf.value.value if pf.value else None
        } for pf in obj.features.all().select_related('feature', 'value')]
    
    def get_tag_groups(self, obj):
        result = []
        for tg in obj.tag_groups.all().prefetch_related('tags'):
            result.append({
                'id': tg.id,
                'group_name_id': tg.group_name_id,
                'group_name_text': tg.group_name.name if tg.group_name else None,
                'tag_ids': list(tg.tags.values_list('id', flat=True))
            })
        return result


class BrandAdminSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'logo_url', 'description', 'created_at', 'products_count']
    
    def get_products_count(self, obj):
        return obj.products.count()
    
    def get_logo_url(self, obj):
        if obj.logo:
            try:
                return obj.logo.url
            except:
                return str(obj.logo)
        return None


class TagAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'category', 'category_name']


class TagNameAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = TagName
        fields = ['id', 'name', 'category', 'category_name', 'created_at']


class FeatureAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Feature
        fields = ['id', 'name', 'category', 'category_name']


class FeatureValueAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = FeatureValue
        fields = ['id', 'value', 'category', 'category_name']


class NewsAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsItem
        fields = ['id', 'title', 'slug', 'preview', 'content', 'image', 'pub_date', 'is_published']
        read_only_fields = ['pub_date']


class AboutContentAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutContent
        fields = ['id', 'title', 'content', 'image', 'updated_at']
        read_only_fields = ['updated_at']


class ContactInfoAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['id', 'phone', 'email', 'address', 'map_url', 'updated_at']
        read_only_fields = ['updated_at']


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'created_at', 'is_processed']
        read_only_fields = ['name', 'email', 'message', 'created_at']


class ImageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'product', 'image', 'is_main', 'order']


# ============ AUTH SERIALIZERS ============
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']