from django.shortcuts import render, reverse, redirect
from django.shortcuts import render
from books.models import Books
from books.enums import *
from django.core.paginator import Paginator
from rest_framework import mixins
from books.serializers import BooksSerializer
from rest_framework import viewsets
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
import logging
logger = logging.getLogger('django.request')

class BooksListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BooksSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)
    queryset = Books.objects.all()

from django.views.decorators.cache import cache_page
#@cache_page(60, key_prefix="bookstore-index")
def index(request):
    '''显示首页'''
    # 查询每个种类的3个新品信息和4个销量最好的商品信息
    logger.info(request.body)
    python_new = Books.objects.get_books_by_type(PYTHON, limit=3, sort='new')
    python_hot = Books.objects.get_books_by_type(PYTHON, limit=4, sort='hot')
    javascript_new = Books.objects.get_books_by_type(JAVASCRIPT,limit=3, sort='new')
    javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, limit=4, sort='hot')
    algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, limit=3, sort='new')
    algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, limit=4, sort='hot')
    machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, limit=3, sort='new')
    machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, limit=4, sort='hot')
    operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, limit=3, sort='new')
    operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, limit=4, sort='hot')
    database_new = Books.objects.get_books_by_type(DATABASE, limit=3, sort='new')
    database_hot = Books.objects.get_books_by_type(DATABASE, limit=4, sort='hot')

    # 定义模板上下文
    context = {
        'python_new': python_new,
        'python_hot': python_hot,
        'javascript_new': javascript_new,
        'javascript_hot': javascript_hot,
        'algorithms_new': algorithms_new,
        'algorithms_hot': algorithms_hot,
        'machinelearning_new': machinelearning_new,
        'machinelearning_hot': machinelearning_hot,
        'operatingsystem_new': operatingsystem_new,
        'operatingsystem_hot': operatingsystem_hot,
        'database_new': database_new,
        'database_hot': database_hot,
    }
    # 使用模板
    return render(request, 'books/index.html', context)

def detail(request, books_id):
    '''显示商品的详情页面'''
    # 获取商品的详情信息
    books = Books.objects.get_books_by_id(books_id=books_id)

    if books is None:
        # 商品不存在，跳转到首页
        return redirect(reverse('books:index'))

    # 新品推荐
    books_li = Books.objects.get_books_by_type(type_id=books.type_id, limit=2, sort='new')
    
    # 当前商品类型
    type_title = BOOKS_TYPE[books.type_id]

    # 用户登录之后，才记录浏览记录
    # 每个用户浏览记录对应redis中的一条信息 格式:'history_用户id':[10,9,2,3,4]
    # [9, 10, 2, 3, 4]
    if request.session.has_key('islogin'):
        # 用户已登录，记录浏览记录
        conn = get_redis_connection('default')
        key = 'history_%d' % request.session.get('passport_id')
        # 先从redis列表中移除books.id
        conn.lrem(key, 0, books.id)
        conn.lpush(key, books.id)
        # 保存用户最近浏览的5个商品
        conn.ltrim(key, 0, 4)

    
    # 定义上下文
    context = {
        'books': books,
        'books_li': books_li,
        'type_title':type_title
    }

    # 使用模板
    return render(request, 'books/detail.html', context)

from django.core.paginator import Paginator

def list(request, type_id, page):
    sort = request.GET.get('sort', 'default')

    if int(type_id) not in BOOKS_TYPE.keys():
        return redirect(reverse('books:index'))

    books_li = Books.objects.get_books_by_type(type_id=type_id, sort=sort)

    paginator = Paginator(books_li, 1)

    num_pages = paginator.num_pages

    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)

    books_li = paginator.page(page)

    if num_pages < 5:
        pages = range(1, num_pages+1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages-4, num_pages+1)
    else:
        pages = range(page-2, page+3)

    books_new = Books.objects.get_books_by_type(type_id=type_id, limit=2, sort='new')

    type_title = BOOKS_TYPE[int(type_id)]
    context = {
        'books_li': books_li,
        'books_new': books_new,
        'type_id': type_id,
        'sort': sort,
        'type_title': type_title,
        'pages': pages
    }

    # 使用模板
    return render(request, 'books/list.html', context)
