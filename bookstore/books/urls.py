from django.conf.urls import url
from books import views

urlpatterns = [
    url(r'^$', views.index, name='index'), # 首页
    url(r'books/(?P<books_id>\d+)/$', views.detail, name='detail'), # 详情页
]
