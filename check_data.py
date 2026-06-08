#!/usr/bin/env python
"""
Быстрая проверка данных в базе для тестирования админ-панели
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Product, Category, Brand, Image

print("=" * 60)
print("СТАТИСТИКА БАЗЫ ДАННЫХ")
print("=" * 60)

categories = Category.objects.all()
brands = Brand.objects.all()
products = Product.objects.all()
images = Image.objects.all()

print(f"\n📁 Категорий: {categories.count()}")
for cat in categories[:5]:
    print(f"   - {cat.name} (slug: {cat.slug})")

print(f"\n🏷️  Брендов: {brands.count()}")
for brand in brands[:5]:
    print(f"   - {brand.name} (slug: {brand.slug})")

print(f"\n📦 Товаров: {products.count()}")
for prod in products[:5]:
    print(f"   - {prod.name} (категория: {prod.category.name}, бренд: {prod.brand})")

print(f"\n🖼️  Изображений: {images.count()}")

print("\n" + "=" * 60)
print("ПРИМЕР ТОВАРА (детально)")
print("=" * 60)

if products.exists():
    product = products.first()
    print(f"\nНазвание: {product.name}")
    print(f"Slug: {product.slug}")
    print(f"Категория: {product.category}")
    print(f"Бренд: {product.brand}")
    print(f"Цена: {product.price}")
    print(f"В наличии: {product.is_available}")
    print(f"Артикул (производителя): {product.manufacturer_sku}")
    print(f"Артикул (внутренний): {product.internal_sku}")
    print(f"Изображений: {product.images.count()}")
    print(f"Главное изображение: {product.images.filter(is_main=True).first()}")
    print(f"Характеристик: {product.features.count()}")

print("\n✅ Всё готово для тестирования админ-панели!\n")
