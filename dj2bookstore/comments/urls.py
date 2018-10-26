from django.urls import path 
from comments import views

app_name = 'comments'
urlpatterns = [
    path('<book_id>/', views.new_comment, name='comment'), # 评论内容
    path('submit/', views.submit, name='submit'),
]
