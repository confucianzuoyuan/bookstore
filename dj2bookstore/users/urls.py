from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('register_handle/', views.register_handle, name='register_handle'), # 用户注册处理
    path('login/', views.login, name='login'), # 显示登陆页面
    path('login_check/', views.login_check, name='login_check'), # 用户登录校验
    path('logout/', views.logout, name='logout'), # 退出用户登录
    path('', views.user, name='user'), # 用户中心-信息页
    path('address/', views.address, name='address'), # 用户中心-地址页
    path('order/', views.order, name='order'), # 用户中心-订单页
    path('verifycode/', views.verifycode, name='verifycode'), # 验证码功能
    path('active/<token>/', views.register_active, name='active'), # 用户激活
]
