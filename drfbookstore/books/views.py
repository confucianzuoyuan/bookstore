from django.shortcuts import render

from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from .models import Books
from rest_framework import mixins
from rest_framework import generics
from rest_framework import viewsets
from .serializers import BooksSerializer

class BooksPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    page_query_param = "page"
    max_page_size = 100


class BooksListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BooksSerializer
    pagination_class = BooksPagination
    queryset = Books.objects.all()
