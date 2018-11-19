"""bookstore URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token
from books.views import BooksListViewSet

router = DefaultRouter()

router.register(r'books', BooksListViewSet, base_name="books")

urlpatterns = [
    url(r'^search/', include('haystack.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^user/', include('users.urls', namespace='user')), # 用户模块
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^login/', obtain_jwt_token),
    url(r'^cart/', include('cart.urls', namespace='cart')),
    url(r'^order/', include('order.urls', namespace='order')),
    url(r'^', include('books.urls', namespace='books')),
]
