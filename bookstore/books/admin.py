from django.contrib import admin
from books.models import Books
# Register your models here.

admin.site.register(Books) # 在admin中添加有关商品的编辑功能。
