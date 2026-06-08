#!/usr/bin/env python
"""
Скрипт для проверки настроек безопасности перед деплоем
Запуск: python security_check.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command

def check_security():
    """Проверка критичных настроек безопасности"""
    
    print("="*60)
    print("🔒 ПРОВЕРКА БЕЗОПАСНОСТИ DJANGO")
    print("="*60)
    print()
    
    issues = []
    warnings = []
    
    # 1. Проверка DEBUG
    if settings.DEBUG:
        issues.append("❌ DEBUG=True - ОПАСНО для production!")
        print("❌ DEBUG: True (ОПАСНО для production!)")
    else:
        print("✅ DEBUG: False")
    
    # 2. Проверка SECRET_KEY
    default_key = 'django-insecure-zo(g8-19uk$1amqpb5obk!@=)fdt-=mv7n3voxe-#zhz#k!0x('
    if settings.SECRET_KEY == default_key:
        issues.append("❌ SECRET_KEY использует значение по умолчанию - КРИТИЧНО!")
        print("❌ SECRET_KEY: Default (КРИТИЧНО!)")
    elif len(settings.SECRET_KEY) < 50:
        warnings.append("⚠️  SECRET_KEY слишком короткий")
        print("⚠️  SECRET_KEY: Слишком короткий")
    else:
        print("✅ SECRET_KEY: OK")
    
    # 3. Проверка ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
        issues.append("❌ ALLOWED_HOSTS не настроен или разрешает все")
        print("❌ ALLOWED_HOSTS: Не настроен")
    else:
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # 4. Проверка CORS
    if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS') and settings.CORS_ALLOW_ALL_ORIGINS:
        issues.append("❌ CORS_ALLOW_ALL_ORIGINS=True - разрешены все домены!")
        print("❌ CORS: Разрешены ВСЕ домены (ОПАСНО!)")
    else:
        print(f"✅ CORS: Ограничено {len(settings.CORS_ALLOWED_ORIGINS)} доменами")
        for origin in settings.CORS_ALLOWED_ORIGINS:
            if origin.startswith('http://') and not settings.DEBUG:
                warnings.append(f"⚠️  CORS разрешает HTTP: {origin}")
    
    # 5. Проверка HTTPS настроек
    if not settings.DEBUG:
        if not settings.SECURE_SSL_REDIRECT:
            warnings.append("⚠️  SECURE_SSL_REDIRECT отключен")
            print("⚠️  HTTPS Redirect: Выключен")
        else:
            print("✅ HTTPS Redirect: Включен")
            
        if settings.SECURE_HSTS_SECONDS < 31536000:
            warnings.append("⚠️  HSTS срок меньше 1 года")
            print(f"⚠️  HSTS: {settings.SECURE_HSTS_SECONDS}s (рекомендуется 31536000)")
        else:
            print("✅ HSTS: 1 year")
    
    # 6. Проверка Cookies
    if not settings.DEBUG:
        if not settings.SESSION_COOKIE_SECURE:
            warnings.append("⚠️  SESSION_COOKIE_SECURE отключен")
            print("⚠️  Session Cookie Secure: Выключен")
        else:
            print("✅ Session Cookie Secure: Включен")
            
        if not settings.CSRF_COOKIE_SECURE:
            warnings.append("⚠️  CSRF_COOKIE_SECURE отключен")
            print("⚠️  CSRF Cookie Secure: Выключен")
        else:
            print("✅ CSRF Cookie Secure: Включен")
    
    # 7. Проверка базы данных
    db_engine = settings.DATABASES['default']['ENGINE']
    if 'sqlite' in db_engine and not settings.DEBUG:
        warnings.append("⚠️  Используется SQLite в production (рекомендуется PostgreSQL)")
        print("⚠️  Database: SQLite (рекомендуется PostgreSQL)")
    else:
        print(f"✅ Database: {db_engine.split('.')[-1]}")
    
    # 8. Middleware проверка
    required_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    
    for middleware in required_middleware:
        if middleware not in settings.MIDDLEWARE:
            issues.append(f"❌ Отсутствует {middleware}")
    
    print(f"✅ Security Middleware: {len([m for m in required_middleware if m in settings.MIDDLEWARE])}/{len(required_middleware)}")
    
    # 9. Проверка статических файлов
    if hasattr(settings, 'STATICFILES_STORAGE'):
        print(f"✅ Static Files Storage: Configured")
    
    print()
    print("="*60)
    
    # Вывод итогов
    if issues:
        print("🚨 КРИТИЧНЫЕ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"  {issue}")
        print()
    
    if warnings:
        print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print()
    
    # Django встроенная проверка
    print("="*60)
    print("🔍 Django встроенная проверка безопасности:")
    print("="*60)
    print()
    
    try:
        call_command('check', '--deploy', '--fail-level', 'WARNING')
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
    
    print()
    print("="*60)
    print("📋 РЕКОМЕНДАЦИИ:")
    print("="*60)
    print()
    print("1. Установите переменные окружения:")
    print("   - SECRET_KEY (сгенерируйте новый)")
    print("   - DEBUG=False")
    print("   - DATABASE_URL (для PostgreSQL)")
    print()
    print("2. Используйте PostgreSQL вместо SQLite")
    print("3. Настройте HTTPS сертификат")
    print("4. Настройте регулярные бэкапы")
    print("5. Мониторинг (Sentry, CloudWatch)")
    print()
    print("Подробнее: см. SECURITY_CHECKLIST.md")
    print("="*60)
    
    return len(issues) == 0

if __name__ == '__main__':
    success = check_security()
    sys.exit(0 if success else 1)
