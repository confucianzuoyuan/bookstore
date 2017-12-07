from django.conf.urls import url
from comments import views

urlpatterns = [
    url(r'comment/(?P<books_id>\d+)/$', views.comment, name='comment'), # 评论内容
]