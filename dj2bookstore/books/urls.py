from books import views
from django.urls import path

app_name = 'books'
urlpatterns = [
    path('', views.index, name='index'), # 首页
    path('books/<int:books_id>/', views.detail, name='detail'), # 详情页
    path('list/<int:type_id>/<int:page>/', views.list, name='list'), # 列表页
]
