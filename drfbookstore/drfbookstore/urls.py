from django.views.static import serve
from rest_framework.documentation import include_docs_urls

from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import TemplateView
from drfbookstore.settings import MEDIA_ROOT
from books.views import BooksListViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# 配置goods的url,这个basename是干啥的
router.register(r'books', BooksListViewSet, base_name="books")

urlpatterns = [
    path('admin/', admin.site.urls),
    # 处理图片显示的url,使用Django自带serve,传入参数告诉它去哪个路径找，我们有配置好的路径MEDIAROOT
    re_path('media/(?P<path>.*)', serve, {"document_root": MEDIA_ROOT }),
    # router的path路径
    re_path('^', include(router.urls)),
    # 自动化文档,1.11版本中注意此处前往不要加$符号
    path('docs/', include_docs_urls(title='书城文档')),
]

