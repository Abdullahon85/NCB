from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    CategoryViewSet,
    ProductViewSet,
    NewsViewSet,
    AboutContentView,
    ContactInfoView,
    ContactMessageView,
    BrandViewSet,
    TagViewSet,
    features_tags_by_category,
    # Admin ViewSets
    ProductAdminViewSet,
    CategoryAdminViewSet,
    BrandAdminViewSet,
    TagAdminViewSet,
    TagNameAdminViewSet,
    FeatureAdminViewSet,
    FeatureValueAdminViewSet,
    NewsAdminViewSet,
    ImageAdminViewSet,
    AboutContentAdminView,
    ContactInfoAdminView,
    ContactMessageAdminViewSet,
    # Auth views
    admin_login,
    admin_logout,
    admin_me,
    admin_change_password,
    admin_update_profile,
    admin_stats,
)

router = DefaultRouter()
# Публичные endpoints
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'news', NewsViewSet)
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'tags', TagViewSet, basename='tag')

# Admin endpoints
router.register(r'admin/products', ProductAdminViewSet, basename='admin-products')
router.register(r'admin/categories', CategoryAdminViewSet, basename='admin-categories')
router.register(r'admin/brands', BrandAdminViewSet, basename='admin-brands')
router.register(r'admin/tags', TagAdminViewSet, basename='admin-tags')
router.register(r'admin/tag-names', TagNameAdminViewSet, basename='admin-tag-names')
router.register(r'admin/features', FeatureAdminViewSet, basename='admin-features')
router.register(r'admin/feature-values', FeatureValueAdminViewSet, basename='admin-feature-values')
router.register(r'admin/news', NewsAdminViewSet, basename='admin-news')
router.register(r'admin/images', ImageAdminViewSet, basename='admin-images')
router.register(r'admin/messages', ContactMessageAdminViewSet, basename='admin-messages')

urlpatterns = [
    path('', include(router.urls)),
    # Публичные endpoints
    path('about/', AboutContentView.as_view(), name='about-content'),
    path('contact/', ContactInfoView.as_view(), name='contact-info'),
    path('contact/message/', ContactMessageView.as_view(), name='contact-message'),
    path('products/by-feature/', views.products_by_feature_value, name='products-by-feature'),
    path('features-tags-by-category/', features_tags_by_category, name='features_tags_by_category'),
    # Admin endpoints
    path('admin/about/', AboutContentAdminView.as_view(), name='admin-about'),
    path('admin/contact/', ContactInfoAdminView.as_view(), name='admin-contact'),
    path('admin/stats/', admin_stats, name='admin-stats'),
    # Auth endpoints
    path('admin/auth/login/', admin_login, name='admin-login'),
    path('admin/auth/logout/', admin_logout, name='admin-logout'),
    path('admin/auth/me/', admin_me, name='admin-me'),
    path('admin/auth/change-password/', admin_change_password, name='admin-change-password'),
    path('admin/auth/profile/', admin_update_profile, name='admin-profile'),
]