from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'), # 用户注册
    url(r'^register_handle/$', views.register_handle, name='register_handle'), # 用户注册处理
    url(r'^login/$', views.login, name='login'),
    url(r'^login_check/$', views.login_check, name='login_check'),
    url(r'^logout/$', views.logout, name='logout'), # 退出用户登录
    url(r'^address/$', views.address, name='address'),
    url(r'^order/(?P<page>\d+)?/?$', views.order, name='order'),
    url(r'^active/(?P<token>.*)/$', views.register_active, name='active'),
    url(r'^verifycode/$', views.verifycode, name='verifycode'),
    url(r'^$', views.user, name='user'), # 用户中心-信息页
]
