# api/admin.py
from django.contrib import admin
from .models import (
    Tag, Category, Product, Image, Feature, ProductFeature, TagName, FeatureValue,
    NewsItem, AboutContent, ContactInfo, ContactMessage, Brand, ProductTagGroup, Banner,
    Order, OrderItem, ProductReview, ProductQuestion
)
from django import forms

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id','name','slug')
    search_fields = ('name','slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(TagName)
class TagNameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

class FeatureValueForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        label='Категория'
    )

    class Meta:
        model = FeatureValue
        fields = ['category', 'value']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.category = self.cleaned_data['category']
        if commit:
            instance.save()
        return instance

@admin.register(FeatureValue)
class FeatureValueAdmin(admin.ModelAdmin):
    form = FeatureValueForm
    list_display = ('id', 'category', 'value')
    list_filter = ('category',)
    search_fields = ('value',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'value')
        }),
    )

# Inline для изображений продукта
class ImageInline(admin.TabularInline):
    model = Image
    extra = 1

class ProductTagGroupForm(forms.ModelForm):
    class Meta:
        model = ProductTagGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product = getattr(self.instance, 'product', None)
        if not product:
            product = self.initial.get('product')
        if product and getattr(product, 'category', None):
            self.fields['tags'].queryset = Tag.objects.filter(category=product.category)
            self.fields['group_name'].queryset = TagName.objects.filter(category=product.category)
        else:
            self.fields['tags'].queryset = Tag.objects.all()
            self.fields['group_name'].queryset = TagName.objects.all()

class ProductTagGroupInline(admin.TabularInline):
    model = ProductTagGroup
    form = ProductTagGroupForm
    extra = 1
    verbose_name_plural = 'Группы тегов товара'
    fields = ['group_name', 'tags']
    autocomplete_fields = ('group_name',)

# Inline для характеристик продукта
class ProductFeatureForm(forms.ModelForm):
    class Meta:
        model = ProductFeature
        fields = ['feature', 'value']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product = getattr(self.instance, 'product', None)
        if not product:
            product = self.initial.get('product')
        if product and getattr(product, 'category', None):
            # Фильтруем характеристики по категории товара
            self.fields['feature'].queryset = Feature.objects.filter(
                category=product.category
            )
            # Фильтруем значения по категории товара через поле category
            self.fields['value'].queryset = FeatureValue.objects.filter(
                category=product.category
            )
        else:
            self.fields['feature'].queryset = Feature.objects.all()
            self.fields['value'].queryset = FeatureValue.objects.all()

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    form = ProductFeatureForm
    extra = 1
    fields = ('feature', 'value')
    autocomplete_fields = ('feature', 'value')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name','slug','created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'slug']
    list_filter = ['parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'internal_sku', 'manufacturer_sku',
        'category', 'price', 'is_available', 'created_at'
    ]
    list_filter = ['brand','category', 'is_available', 'created_at',]
    search_fields = ['name', 'description', 'internal_sku', 'manufacturer_sku', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ImageInline, ProductFeatureInline, ProductTagGroupInline]
    date_hierarchy = 'created_at'
    autocomplete_fields = ('brand',)

    class Media:
        js = ('admin/js/filter_features.js',)

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'pub_date', 'is_published']
    list_filter = ['is_published', 'pub_date']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'pub_date'

@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'updated_at']
    
    def has_add_permission(self, request):
        # Разрешить добавление только если нет записей
        return not AboutContent.objects.exists()

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['phone', 'email', 'updated_at']
    
    def has_add_permission(self, request):
        # Разрешить добавление только если нет записей
        return not ContactInfo.objects.exists()

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at', 'is_processed']
    list_filter = ['is_processed', 'created_at']
    search_fields = ['name', 'email', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['name', 'email', 'message', 'created_at']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'product', 'rating', 'is_published', 'created_at']
    list_filter = ['is_published', 'rating', 'created_at']
    search_fields = ['author_name', 'text']
    list_editable = ['is_published']
    readonly_fields = ['author_name', 'product', 'rating', 'text', 'created_at']


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'product', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['author_name', 'text']
    list_editable = ['is_published']
    readonly_fields = ['author_name', 'product', 'text', 'created_at']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['order']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_sku', 'price', 'quantity']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_phone', 'customer_email', 'status', 'items_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'customer_phone', 'customer_email']
    readonly_fields = ['customer_name', 'customer_phone', 'customer_email', 'comment', 'created_at']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    ordering = ['-created_at']

    @admin.display(description='Позиций')
    def items_count(self, obj):
        return obj.items.count()
