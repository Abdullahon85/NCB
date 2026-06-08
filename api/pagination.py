# api/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12                 # количество объектов на страницу по умолчанию
    page_size_query_param = 'page_size'  # позволяет клиенту указать ?page_size=20
    max_page_size = 100            # ограничение сверху
