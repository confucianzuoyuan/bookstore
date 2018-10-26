from django.urls import path 
from order import views

app_name = 'order'
urlpatterns = [
    path('place/', views.order_place, name='place'), # 订单提交页面
    path('commit/', views.order_commit, name='commit'), # 生成订单
    path('pay/', views.order_pay, name='pay'), # 订单支付
    path('check_pay/', views.check_pay, name='check_pay'), # 查询支付结果
]

