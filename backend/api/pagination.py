from rest_framework import pagination


class FoodgramPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
