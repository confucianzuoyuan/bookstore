from django.conf.urls import url
from comments import views

urlpatterns = [
    url(r'^(?P<book_id>\d+)/$', views.new_comment, name='comment'), # 评论内容
    url(r'^submit/$', views.submit, name='submit')
]