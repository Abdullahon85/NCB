#models.py
from django.db import models
from django.utils.text import slugify
from django.core.validators import URLValidator
import random
from django.db import transaction, IntegrityError


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,related_name='children',verbose_name='Родительская категория')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение')
    order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_all_products(self):
        """Получить все товары категории включая подкатегории (оптимизировано)"""
        categories = [self]
        children = list(self.children.all())
        while children:
            child = children.pop()
            categories.append(child)
            children.extend(list(child.children.all()))
        return Product.objects.filter(category__in=categories).select_related(
            'category', 'brand'
        ).prefetch_related('images')

class Brand(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)  # 👈 добавь
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:160]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, blank=True, related_name='products')
    description = models.TextField(verbose_name='Описание')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products',verbose_name='Категория')
    price = models.DecimalField(max_digits=25, decimal_places=2, null=True, blank=True, verbose_name='Цена')
    is_available = models.BooleanField(default=True, verbose_name='В наличии')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    manufacturer_sku = models.CharField(max_length=100, blank=True, null=True, verbose_name='Артикул производителя')
    internal_sku = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name='Внутренний SKU')
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.internal_sku:
            # префикс: три буквы из slug категории или из названия
            raw_prefix = (self.category.slug if self.category and self.category.slug else self.name[:3])
            prefix = ''.join(ch for ch in raw_prefix.upper() if ch.isalnum())[:3] or 'PRD'

            attempts = 0
            while attempts < 10:
                number = str(random.randint(0, 10**4 - 1)).zfill(4)  # 4-значная числовая часть
                candidate = f"{prefix}-{number}"
                self.internal_sku = candidate
                try:
                    # пробуем сохранить в транзакции, чтобы поймать unique constraint
                    with transaction.atomic():
                        super().save(*args, **kwargs)
                    return
                except IntegrityError:
                    attempts += 1
                    # повторяем с новым candidate
                    continue
            # если не удалось — выбрасываем ошибку чтобы не сохранить неконсистентные данные
            raise IntegrityError("Не удалось сгенерировать уникальный internal_sku")
        # если internal_sku уже есть — обычное сохранение
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class FeatureValue(models.Model):
    """Модель для значений характеристик"""
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='feature_values',
        verbose_name='Категория',
        null=True,
        blank=True
    )
    value = models.CharField(max_length=500, verbose_name='Значение')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Значение характеристики'
        verbose_name_plural = 'Значения характеристик'
        unique_together = ['category', 'value']  # Уникальность в рамках категории
        ordering = ['value']

    def __str__(self):
        return self.value


class Feature(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название характеристики')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='feature', verbose_name='Категория')
    values = models.ManyToManyField(
        FeatureValue, 
        related_name='features', 
        blank=True,
        verbose_name='Значения'
    )
    
    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'
        unique_together = [['name', 'category']]  # Уникальность в рамках категории

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class ProductFeature(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='features',   # оставляем как было
        verbose_name='Товар'
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='product_features',  # <- ОБЯЗАТЕЛЬНО уникальное имя
        verbose_name='Характеристика',
        null=True,
        blank=True,
    )
    value = models.ForeignKey(
        FeatureValue,
        on_delete=models.CASCADE,
        verbose_name='Значение',
        null=True,
        blank=True,
        related_name='product_features'
    )

    class Meta:
        verbose_name = 'Характеристика товара'
        verbose_name_plural = 'Характеристики товаров'

    def __str__(self):
        return f'{self.feature.name if self.feature else "N/A"}: {self.value if self.value else "N/A"}'

class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name='Тег')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='tags',
        null=True,
        blank=True,
        verbose_name='Категория'
    )
    tag_name = models.ForeignKey(
        'TagName',
        on_delete=models.SET_NULL,
        related_name='tags',
        null=True,
        blank=True,
        verbose_name='Группа тега'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']
        unique_together = ['tag_name', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __str__(self):
        return self.name

class TagName(models.Model):
    """Модель для имен тегов"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Имя тега')
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='tag_names',
        null=True,
        blank=True,
        verbose_name='Категория'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Имя тега'
        verbose_name_plural = 'Имена тегов'
        ordering = ['name']

    def __str__(self):
        return self.name

class ProductTagGroup(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='tag_groups',
        verbose_name='Товар'
    )
    group_name = models.ForeignKey(
        'TagName',
        on_delete=models.CASCADE,
        verbose_name='Название тега',
        null=True,
        blank=True,
        related_name='producttaggroup_group_name'
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        verbose_name='Теги',
        related_name='producttaggroup_tags'
    )

    class Meta:
        verbose_name = 'Группа тегов товара'
        verbose_name_plural = 'Группы тегов товара'

    def __str__(self):
        return self.group_name.name if self.group_name else "Без названия"

class Image(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name='Товар'
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    is_main = models.BooleanField(default=False, verbose_name='Главное изображение')
    order = models.IntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['order']

    def __str__(self):
        return f'Изображение для {self.product.name}'


class NewsItem(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField(verbose_name='Содержание')
    preview = models.TextField(max_length=500, verbose_name='Краткое описание')
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name='Изображение')
    image = models.URLField(blank=True)
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-pub_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class AboutContent(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='about/', blank=True, null=True, verbose_name='Изображение')
    image = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Страница "О нас"'
        verbose_name_plural = 'Страница "О нас"'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk and AboutContent.objects.exists():
            raise ValueError('Может существовать только одна запись AboutContent')
        super().save(*args, **kwargs)


class ContactInfo(models.Model):
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    address = models.TextField(verbose_name='Адрес')
    map_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на карту')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'

    def __str__(self):
        return 'Контактная информация'

    def save(self, *args, **kwargs):
        if not self.pk and ContactInfo.objects.exists():
            raise ValueError('Может существовать только одна запись ContactInfo')
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    is_processed = models.BooleanField(default=False, verbose_name='Обработано')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']

    def __str__(self):
        return f'Сообщение от {self.name} ({self.created_at.strftime("%d.%m.%Y")})'


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]
    customer_name = models.CharField(max_length=150, verbose_name='Имя заказчика')
    customer_phone = models.CharField(max_length=50, verbose_name='Телефон')
    customer_email = models.EmailField(blank=True, verbose_name='Email')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} от {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_items', verbose_name='Товар'
    )
    product_name = models.CharField(max_length=200, verbose_name='Название товара')
    product_sku = models.CharField(max_length=100, blank=True, verbose_name='Артикул')
    price = models.DecimalField(
        max_digits=25, decimal_places=2, null=True, blank=True, verbose_name='Цена'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'


class Banner(models.Model):
    """Баннер для слайдера на главной странице"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    image = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name='Изображение')
    link = models.CharField(max_length=500, blank=True, null=True, verbose_name='Ссылка')
    order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title