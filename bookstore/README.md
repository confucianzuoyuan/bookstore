# 目录

- [1，新建项目](#1)
- [2，用户系统开发](#2)
- [3，书籍商品模块](#3)
- [4，用户中心实现](#4)
- [5，购物车功能](#5)
- [6，订单页面的开发](#6)
- [7，使用缓存](#7)
- [8，评论功能](#8)
- [9，发送邮件功能实现](#9)
- [10，登陆验证码功能实现](#10)
- [11，全文检索的实现](#11)
- [12，用户激活功能实现](#12)
- [13，用户中心最近浏览功能](#13)
- [14，过滤器功能实现](#14)
- [15，使用nginx+gunicorn+django进行部署](#15)
- [16，django日志模块的使用](#16)
- [17，中间件的编写](#17)

# <a id="1">1，新建项目</a>

## 1，新建项目
```
$ django-admin startproject bookstore
```

## 2，将需要用的包添加进来

```
# wq保存
$ vim requirements.txt
```

安装包文件如下:

```python
# requirements.txt
amqp==2.2.2
billiard==3.5.0.3
celery==4.1.0
Django==1.8.2
django-haystack==2.6.1
django-redis==4.8.0
django-tinymce==2.6.0
itsdangerous==0.24
jieba==0.39
kombu==4.1.0
olefile==0.44
Pillow==4.3.0
pycryptodome==3.4.7
PyMySQL==0.7.11
python-alipay-sdk==1.7.0
pytz==2017.2
redis==2.10.6
uWSGI==2.0.15
vine==1.1.4
Whoosh==2.7.4
```

安装环境（在虚拟环境中）

```
$ pip install -r requirements.txt
```

## 3，修改项目配置文件，将默认sqlite改为mysql

```python
# bookstore/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bookstore',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    }
}
```

为了使用mysql的驱动，在根应用的`__init__.py`文件中加入以下两行代码：

```py
import pymysql
pymysql.install_as_MySQLdb()
```

# <a id="2">2，用户系统开发</a>

## 1，用户系统的开发

新建users这个app，也就是用户app，先从注册页做起。

```
$ python manage.py startapp users
```

我们建好users app后，需要将它添加到配置文件中去。

```python
bookstore/settings.py
INSTALLED_APPS = (
    ...
    'users', # 用户模块
)
```

然后我们需要设计表结构，我们要思考一下，这个users数据表结构应该包含哪些字段？
我们需要先抽象出一个BaseModel，一个基本模型，什么意思呢？因为数据表有共同的字段，我们可以把它抽象出来，比如create_at（创建时间），update_at（更新时间），is_delete（软删除）。注意！这个base_model.py要保存在根目录下面的db文件夹中，别忘了db文件夹中的__init__.py。

```python
# bookstore/db/base_model.py
from django.db import models

class BaseModel(models.Model):
    '''模型抽象基类'''
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True
```

然后我们针对Users设计一张表出来。以下代码写入`users/models.py`文件中。

```python
from db.base_model import BaseModel

class Passport(BaseModel):
    '''用户模型类'''
    username = models.CharField(max_length=20, unique=True, verbose_name='用户名称')
    password = models.CharField(max_length=40, verbose_name='用户密码')
    email = models.EmailField(verbose_name='用户邮箱')
    is_active = models.BooleanField(default=False, verbose_name='激活状态')

    # 用户表的管理器
    objects = PassportManager()

    class Meta:
        db_table = 's_user_account'
```

接下来我们在PassportManager()中实现添加和查找账户信息的功能，这样抽象性更好。

```python
# Create your models here.
class PassportManager(models.Manager):
    def add_one_passport(self, username, password, email):
        '''添加一个账户信息'''
        passport = self.create(username=username, password=get_hash(password), email=email)
        # 3.返回passport
        return passport

    def get_one_passport(self, username, password):
        '''根据用户名密码查找账户的信息'''
        try:
            passport = self.get(username=username, password=get_hash(password))
        except self.model.DoesNotExist:
            # 账户不存在
            passport = None
        return passport
```

我们这里有一个get_hash函数，这个函数用来避免存储明文密码。所以我们来编写这个函数。在根目录新建一个文件夹utils，用来存放功能函数，比如get_hash，别忘了__init__.py文件。

```python
# bookstore/utils/get_hash.py
from hashlib import sha1

def get_hash(str):
    '''取一个字符串的hash值'''
    sh = sha1()
    sh.update(str.encode('utf8'))
    return sh.hexdigest()
```

接下来我们将Users的表映射到数据库中去。

```
mysql> create database bookstore charset=utf8;
$ python manage.py makemigrations users
$ python manage.py migrate
```

## 2，用户系统前端模板编写

接下来我们要将前端模板写一下，先建一个模板文件夹。

```
$ mkdir templates
```

我们第一个实现的功能是渲染注册页。将register.html拷贝到templates/users。
将js，css，images文件夹拷贝到static文件夹下。作为静态文件。
接下来我们将程序跑起来。看到了Django的欢迎页面。
```
$ python manage.py runserver 9000
```
然后呢？我们想把register.html渲染出来。我们先来看views.py这个视图文件。
```py
# users/views.py
def register(request):
    '''显示用户注册页面'''
    return render(request, 'users/register.html')
```
然后我们将url映射做好。主应用的urls.py为
```py
# bookstore/urls.py
urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^user/', include('users.urls', namespace='user')), # 用户模块
]
```
'^'表示只匹配user为开头的url。
然后在users app里面的urls配置url映射。
```python
# users/urls.py
from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'), # 用户注册
]
```
将templates的路径写入配置文件中。
```python
# settings.py
TEMPLATES = [
    {
        ...
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # 这里别忘记配置！
        ...
    },
]
```
我们可以看到静态文件没有加载出来，所以我们要改一下html文件中的路径。将静态文件的路径前面加上'/static/'
然后在配置文件中加入调试时使用的静态文件目录。
```python
# settings.py
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
] # 调试时使用的静态文件目录
```
好。我们渲染注册页的任务就完成了。



## 3，注册页面表单提交功能
接下来我们要编写注册页面的提交表单功能。
1，接受前端传过来的表单数据。
2，校验数据。
3，写入数据库。
4，返回注册页（因为还没做首页）。
```python
# users/views.py
def register_handle(request):
    '''进行用户注册处理'''
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')

    # 进行数据校验
    if not all([username, password, email]):
        # 有数据为空
        return render(request, 'users/register.html', {'errmsg': '参数不能为空!'})

    # 判断邮箱是否合法
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        # 邮箱不合法
        return render(request, 'users/register.html', {'errmsg': '邮箱不合法!'})

    # 进行业务处理:注册，向账户系统中添加账户
    # Passport.objects.create(username=username, password=password, email=email)
    try:
        Passport.objects.add_one_passport(username=username, password=password, email=email)
    except:
        return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})

    # 注册完，还是返回注册页。
    return redirect(reverse('user:register'))
```
配置urls.py
```python
# users/urls.py
url(r'^register_handle/$', views.register_handle, name='register_handle'), # 用户注册处理
```
前端使用Form来发送POST请求。
```
<form method="post" action="/user/register_handle/">
```
注意添加csrf_token以及错误信息
```
{% csrf_token %}
{{errmsg}}
```
然后就完成注册功能了。之后需要实现发送激活邮件。

# <a id="3">3，书籍商品模块</a>
## 1，渲染首页功能（书籍表结构设计）
完成注册功能以后，点击注册按钮应该跳转到首页。所以我们把首页index.html完成。先新建一个books app。
```
$ python manage.py startapp books
```
在配置文件中添加books app
```
# bookstore/settings.py
INSTALLED_APPS = (
    ...
    'users', # 用户模块
    'books', # 商品模块
)
```
然后设计models，也就是books模块的表结构。这里我们先介绍一下富文本编辑器，因为编辑商品详情页需要使用富文本编辑器。

### 富文本编辑器应用到项目中

- 在settings.py中为INSTALLED_APPS添加编辑器应用
``` python
# settings.py
INSTALLED_APPS = (
    ...
    'tinymce',
)
```

- 在settings.py中添加编辑配置项
``` python
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'width': 600,
    'height': 400,
}
```

- 在根urls.py中配置
``` python
urlpatterns = [
    ...
    url(r'^tinymce/', include('tinymce.urls')),
]
```

下面在我们的应用中添加富文本编辑器。
然后我们就可以设计我们的商品表结构了，我们可以通过观察detail.html来设计表结构。
我们先把一些常用的常量存储到books/enums.py文件中

```python
PYTHON = 1
JAVASCRIPT = 2
ALGORITHMS = 3
MACHINELEARNING = 4
OPERATINGSYSTEM = 5
DATABASE = 6

BOOKS_TYPE = {
    PYTHON: 'Python',
    JAVASCRIPT: 'Javascript',
    ALGORITHMS: '数据结构与算法',
    MACHINELEARNING: '机器学习',
    OPERATINGSYSTEM: '操作系统',
    DATABASE: '数据库',
}

OFFLINE = 0
ONLINE = 1

STATUS_CHOICE = {
    OFFLINE: '下线',
    ONLINE: '上线'
}
```

然后再来设计表结构：

```python
from db.base_model import BaseModel
from tinymce.models import HTMLField
from books.enums import *
# Create your models here.
class Books(BaseModel):
    '''商品模型类'''
    books_type_choices = ((k, v) for k,v in BOOKS_TYPE.items())
    status_choices = ((k, v) for k,v in STATUS_CHOICE.items())
    type_id = models.SmallIntegerField(default=PYTHON, choices=books_type_choices, verbose_name='商品种类')
    name = models.CharField(max_length=20, verbose_name='商品名称')
    desc = models.CharField(max_length=128, verbose_name='商品简介')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    unit = models.CharField(max_length=20, verbose_name='商品单位')
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    detail = HTMLField(verbose_name='商品详情')
    image = models.ImageField(upload_to='books', verbose_name='商品图片')
    status = models.SmallIntegerField(default=ONLINE, choices=status_choices, verbose_name='商品状态')

    objects = BooksManager()

    # admin显示书籍的名字
    def __str__(self):
        return self.name

    class Meta:
        db_table = 's_books'
        verbose_name = '书籍'
        verbose_name_plural = '书籍'
```

同样，我们这里再写一下BooksManager()，有一些基本功能在这里抽象出来。

```python
class BooksManager(models.Manager):
    '''商品模型管理器类'''
    # sort='new' 按照创建时间进行排序
    # sort='hot' 按照商品销量进行排序
    # sort='price' 按照商品的价格进行排序
    # sort= 按照默认顺序排序
    def get_books_by_type(self, type_id, limit=None, sort='default'):
        '''根据商品类型id查询商品信息'''
        if sort == 'new':
            order_by = ('-create_time',)
        elif sort == 'hot':
            order_by = ('-sales', )
        elif sort == 'price':
            order_by = ('price', )
        else:
            order_by = ('-pk', ) # 按照primary key降序排列。

        # 查询数据
        books_li = self.filter(type_id=type_id).order_by(*order_by)

        # 查询结果集的限制
        if limit:
            books_li = books_li[:limit]
        return books_li

    def get_books_by_id(self, books_id):
        '''根据商品的id获取商品信息'''
        try:
            books = self.get(id=books_id)
        except self.model.DoesNotExist:
            # 不存在商品信息
            books = None
        return books
```

做数据库迁移。

```
$ python manage.py makemigrations books
$ python manage.py migrate
```

好，接下来我们就可以将首页index.html渲染出来了。现在根urls.py中配置url。

```python
url(r'^', include('books.urls', namespace='books')), # 商品模块
```

然后在books app中的urls.py中配置url。

```python
from django.conf.urls import url
from books import views

urlpatterns = [
    url(r'^$', views.index, name='index'), # 首页
]
```

## 2，编写书籍表视图函数。

然后编写视图文件views.py。

```python
# books/views.py
from django.shortcuts import render
from books.models import Books
from books.enums import *
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
# Create your views here.


def index(request):
    '''显示首页'''
    # 查询每个种类的3个新品信息和4个销量最好的商品信息
    python_new = Books.objects.get_books_by_type(PYTHON, limit=3, sort='new')
    python_hot = Books.objects.get_books_by_type(PYTHON, limit=4, sort='hot')
    javascript_new = Books.objects.get_books_by_type(JAVASCRIPT,limit= 3, sort='new')
    javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, limit=4, sort='hot')
    algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, 3, sort='new')
    algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, 4, sort='hot')
    machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, 3, sort='new')
    machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, 4, sort='hot')
    operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, 3, sort='new')
    operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, 4, sort='hot')
    database_new = Books.objects.get_books_by_type(DATABASE, 3, sort='new')
    database_hot = Books.objects.get_books_by_type(DATABASE, 4, sort='hot')

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
```

然后将index.html拷贝到templates/books。


## 3，将Books注册到后台管理系统admin

再将Books这个model注册到admin里面，方便管理，可以用来在后台编辑商品信息。

```python
# books/admin.py
from django.contrib import admin
from books.models import Books
# Register your models here.

admin.site.register(Books) # 在admin中添加有关商品的编辑功能。
```

然后我们创建超级管理员账户。

```
$ python manage.py createsuperuser
```

这样我们就可以登陆admin来管理商品信息了，admin功能是django的杀手锏之一。
接下来我们要把index.html中的文件路径改一下，要不然显示不出来。
我们通过分析模板来改写成后端渲染出来的模板。比如：

```python
{% for book in python_new %}
    <a href="#">{{ book.name }}</a>
{% endfor %}
```
用来替换掉`index.html`中的：
```html
<a href="#">Python核心编程</a>
<a href="#">笨办法学Python</a>
<a href="#">Python学习手册</a>
```

用代码：
```html
{% for book in python_hot %}
    <li>
        <h4><a href="#">{{ book.name }}</a></h4>
        <a href="#"><img src="{% static book.image %}"></a>
        <div class="prize">¥ {{ book.price }}</div>
    </li>
{% endfor %}
```
替换掉`index.html`中的：
```html
<li>
    <h4><a href="#">Python核心编程</a></h4>
    <a href="#"><img src="images/book/book001.jpg"></a>
    <div class="prize">¥ 30.00</div>
</li>
<li>
    <h4><a href="#">Python学习手册</a></h4>
    <a href="#"><img src="images/book/book002.jpg"></a>
    <div class="prize">¥ 5.50</div>
</li>
<li>
    <h4><a href="#">Python Cookbook</a></h4>
    <a href="#"><img src="images/book/book003.jpg"></a>
    <div class="prize">¥ 3.90</div>
</li>
<li>
    <h4><a href="#">Python高性能编程</a></h4>
    <a href="#"><img src="images/book/book004.jpg"></a>
    <div class="prize">¥ 25.80</div>
</li>
```

由于我们在编辑商品信息时，需要上传书籍的图片，所以在配置文件中设置图片存放目录。

```python
# settings.py
MEDIA_ROOT = os.path.join(BASE_DIR, "static")
```

我们将'/static/images/...'的格式改成django里面推荐的用法。
在index.html开头添加

```
{% load staticfiles %}
```

并改写静态文件url格式为：

```
<img src="{% static book.image %}">
```

好，那我们首页的渲染工作也就完成了。

## 4，从注册页跳转到首页
接下来我们将register.html注册完以后，跳转到首页去。

```
# user/views.py
return redirect(reverse('books:index'))
```

做完注册和首页，我们可以来做登陆页面了。将login.html拷贝到templates/users/下。
注意修改静态文件路径。然后编写/users/views.py文件中的login功能。

```python
def login(request):
    '''显示登录页面'''
    if request.COOKIES.get("username"):
        username = request.COOKIES.get("username")
        checked = 'checked'
    else:
        username = ''
        checked = ''
    context = {
        'username': username,
        'checked': checked,
    }

    return render(request, 'users/login.html', context)
```

将url配置到urls.py

```python
url(r'^login/$', views.login, name='login') # 显示登陆页面
```

好，我们显示登陆页面也做完了。

## 5，登陆功能的实现。

我们先来实现登录数据校验的功能。还有记住用户名的功能。

```python
# users/views.py
def login_check(request):
    '''进行用户登录校验'''
    # 1.获取数据
    username = request.POST.get('username')
    password = request.POST.get('password')
    remember = request.POST.get('remember')

    # 2.数据校验
    if not all([username, password, remember]):
        # 有数据为空
        return JsonResponse({'res': 2})

    # 3.进行处理:根据用户名和密码查找账户信息
    passport = Passport.objects.get_one_passport(username=username, password=password)

    if passport:
        next_url = reverse('books:index') # /user/
        jres = JsonResponse({'res': 1, 'next_url': next_url})

        # 判断是否需要记住用户名
        if remember == 'true':
            # 记住用户名
            jres.set_cookie('username', username, max_age=7*24*3600)
        else:
            # 不要记住用户名
            jres.delete_cookie('username')

        # 记住用户的登录状态
        request.session['islogin'] = True
        request.session['username'] = username
        request.session['passport_id'] = passport.id
        return jres
    else:
        # 用户名或密码错误
        return JsonResponse({'res': 0})
```

这个函数在前端发送数据是调用。我们在前端编写一段发送ajax post请求的html代码和jquery代码。将下面这段代码替换掉表单代码：

```html
<form>
  ...
</form>
```

```html
    {% csrf_token %}
    <input type="text" id="username" class="name_input" value="{{ username }}" placeholder="请输入用户名">
    <div class="user_error">输入错误</div>
    <input type="password" id="pwd" class="pass_input" placeholder="请输入密码">
    <div class="pwd_error">输入错误</div>
    <div class="more_input clearfix">
        <input type="checkbox" name="remember" {{ checked }}>
        <label>记住用户名</label>
        <a href="#">忘记密码</a>
    </div>
    <input type="button" id="btnLogin" value="登录" class="input_submit">
```

```html
    <script src="{% static 'js/jquery-1.12.4.min.js' %}"></script>
    <script>
        $(function () {
            $('#btnLogin').click(function () {
                var username = $("#username").val()
                var password = $("#pwd").val()
                var remember = $('input[name="remember"]').prop('checked')
                var csrfmiddlewaretoken = $('input[name="csrfmiddlewaretoken"]').val()

                var params = {
                    username: username,
                    password: password,
                    remember: remember,
                    csrfmiddlewaretoken: csrfmiddlewaretoken
                }
                $.post('/user/login_check/', params, function (data) {
                    // 用户名密码错误 {'res': 0}
                    // 登录成功 {'res': 1}
                    if (data.res == 1) {
                        // 跳转页面
                        location.href = data.next_url;
                    } else if (data.res == 2) {
                        alert("数据不完整");
                    } else if (data.res == 0) {
                        alert("用户名或者密码错误");
                    }
                })
            })
        })
    </script>
```

配置urls.py

```python
url(r'^login_check/$', views.login_check, name='login_check'), # 用户登录校验
```

## 6，首页上的登陆和注册按钮redirect到相关页面。

```html
<a href="{% url 'user:login' %}">登录</a>
<span>|</span>
<a href="{% url 'user:register' %}">注册</a>
```

现在登陆以后还是显示登陆和注册，应该显示用户名才对。我们来修改一下index.html。这里就会用到session这个概念了。顺便把logout功能也实现了。

```python
# /user/logout
def logout(request):
    '''用户退出登录'''
    # 清空用户的session信息
    request.session.flush()
    # 跳转到首页
    return redirect(reverse('books:index'))
```

然后改写index.html

```python
{% if request.session.islogin %}
<div class="login_btn fl">
    欢迎您：<em>{{ request.session.username }}</em>
    <span>|</span>
    <a href="{% url 'user:logout' %}">退出</a>
</div>
{% else %}
<div class="login_btn fl">
    <a href="{% url 'user:login' %}">登录</a>
    <span>|</span>
    <a href="{% url 'user:register' %}">注册</a>
</div>
{% endif %}
```

配置urls.py

```python
url(r'^logout/$', views.logout, name='logout'), # 退出用户登录
```

## 7，实现商品详情页的功能

```python
# books/views.py
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
    
    # 定义上下文
    context = {'books': books, 'books_li': books_li，'type_title':type_title}

    # 使用模板
    return render(request, 'books/detail.html', context)
```

配置urls.py

```python
url(r'books/(?P<books_id>\d+)/$', views.detail, name='detail'), # 详情页
```

将detail.html页面拷贝到templates/books下。
然后将detail.html页面改写成django可以渲染的模板。

```html
#动态添加详情页商品的标签(全部商品下的)
{{type_title}}
```

```html
<h3>{{ books.name }}</h3>
<p>{{ books.desc }}</p>
<div class="price_bar">
    <span class="show_pirze">¥<em>{{ books.price }}</em></span>
    <span class="show_unit">单  位：{{ books.unit }}</span>
</div>
```

```html
{% for book in books_li %}
<li>
    <a href="{% url 'books:detail' books_id=book.id %}"><img src="{% static book.image %}"></a>
    <h4><a href="{% url 'books:detail' books_id=book.id %}">{{ book.name }}</a></h4>
    <div class="price">￥{{ book.price }}</div>
</li>
{% endfor %}
```
然后将静态文件的路径修改。
比如：
```
<img src="{% static books.image %}">
```
然后将登陆后的用户名等显示出来。那商品详情页就开发的差不多了。

## 8，抽象出一个通用的模板，供别的模板继承。
```html
{# 首页 登录 注册 的父模板 #}
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
{% load staticfiles %}
<head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
    {# 网页顶部标题块 #}
    <title>{% block title %}{% endblock title %}</title>
    <link rel="stylesheet" type="text/css" href="{% static 'css/reset.css' %}">
    <link rel="stylesheet" type="text/css" href="{% static 'css/main.css' %}">
    <script type="text/javascript" src="{% static 'js/jquery-1.12.4.min.js' %}"></script>
    <script type="text/javascript" src="{% static 'js/jquery-ui.min.js' %}"></script>
    <script type="text/javascript" src="{% static 'js/slide.js' %}"></script>
    {# 网页顶部引入文件块 #}
    {% block topfiles %}
    {% endblock topfiles %}
</head>
<body>
{# 网页顶部欢迎信息块 #}
{% block header_con %}
    <div class="header_con">
        <div class="header">
            <div class="welcome fl">欢迎来到尚硅谷书店!</div>
            <div class="fr">
                {% if request.session.islogin %}
                <div class="login_btn fl">
                    欢迎您：<em>{{ request.session.username }}</em>
                    <span>|</span>
                    <a href="{% url 'user:logout' %}">退出</a>
                </div>
                {% else %}
                <div class="login_btn fl">
                    <a href="{% url 'user:login' %}">登录</a>
                    <span>|</span>
                    <a href="{% url 'user:register' %}">注册</a>
                </div>
                {% endif %}
                <div class="user_link fl">
                    <span>|</span>
                    <a href="#">用户中心</a>
                    <span>|</span>
                    <a href="#">我的购物车</a>
                    <span>|</span>
                    <a href="#">我的订单</a>
                </div>
            </div>
        </div>      
    </div>
{% endblock header_con %}
{# 网页顶部搜索框块 #}
{% block search_bar %}
    <div class="search_bar clearfix">
        <a href="{% url 'books:index' %}" class="logo fl"><img src="{% static 'images/logo.png' %}" style="width: 160px; height: 53px;"></a>
        <div class="search_con fl">
            <input type="text" class="input_text fl" name="" placeholder="搜索商品">
            <input type="button" class="input_btn fr" name="" value="搜索">
        </div>
        <div class="guest_cart fr">
            <a href="#" class="cart_name fl">我的购物车</a>
            <div class="book_count fl" id="show_count">0</div>
        </div>
    </div>
{% endblock search_bar %}
{# 网页主体内容块 #}
{% block body %}{% endblock body %}

    <div class="footer">
        <div class="foot_link">
            <a href="#">关于我们</a>
            <span>|</span>
            <a href="#">联系我们</a>
            <span>|</span>
            <a href="#">招聘人才</a>
            <span>|</span>
            <a href="#">友情链接</a>
        </div>
        <p>CopyRight © 2016 北京尚硅谷信息技术有限公司 All Rights Reserved</p>
        <p>电话：010-****888    京ICP备*******8号</p>
    </div>
    {# 网页底部html元素块 #}
    {% block bottom %}{% endblock bottom %}
    {# 网页底部引入文件块 #}
    {% block bottomfiles %}{% endblock bottomfiles %}
</body>
</html>
```
然后在别的模板中继承base.html，这就是抽象的好处。现在的组件化思路也是这样的，松耦合，紧内聚，复用的思路。
比如改写register.html
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书城-注册{% endblock title %}
{% block topfiles %}
{% endblock topfiles %}
{% block header_con %}{% endblock header_con %}
{% block search_bar %}{% endblock search_bar %}
{% block body %}
    <div class="register_con">
        <div class="l_con fl">
            <a class="reg_logo"><img src="/static/images/logo.png" style="width: 160px; height: 53px;"></a>
            <div class="reg_slogan">学计算机  ·  来尚硅谷</div>
            <div class="reg_banner"></div>
        </div>

        <div class="r_con fr">
            <div class="reg_title clearfix">
                <h1>用户注册</h1>
                <a href="#">登录</a>
            </div>
            <div class="reg_form clearfix">
                <form method="post" action="/user/register_handle/">
                    {% csrf_token %}
                <ul>
                    <li>
                        <label>用户名:</label>
                        <input type="text" name="user_name" id="user_name">
                        <span class="error_tip">提示信息</span>
                    </li>
                    <li>
                        <label>密码:</label>
                        <input type="password" name="pwd" id="pwd">
                        <span class="error_tip">提示信息</span>
                    </li>
                    <li>
                        <label>确认密码:</label>
                        <input type="password" name="cpwd" id="cpwd">
                        <span class="error_tip">提示信息</span>
                    </li>
                    <li>
                        <label>邮箱:</label>
                        <input type="text" name="email" id="email">
                        <span class="error_tip">提示信息</span>
                    </li>
                    <li class="agreement">
                        <input type="checkbox" name="allow" id="allow" checked="checked">
                        <label>同意”尚硅谷书城用户使用协议“</label>
                        <span class="error_tip2">提示信息</span>
                    </li>
                    <li class="reg_sub">
                        <input type="submit" value="注 册" name="">
                        {{errmsg}}
                    </li>
                </ul>
                </form>
            </div>

        </div>

    </div>
{% endblock body %}
```
然后改写login.html
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书城-登录{% endblock title %}
{% block topfiles %}
<script>
    $(function () {
        $('#btnLogin').click(function () {
            // 获取用户名和密码
            var username = $('#username').val()
            var password = $('#pwd').val()
            var csrf = $('input[name="csrfmiddlewaretoken"]').val()
            var remember = $('input[name="remember"]').prop('checked')
            // 发起ajax请求
            var params = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf,
                'remember': remember
            }
            $.post('/user/login_check/', params, function (data) {
                // 用户名密码错误 {'res':0}
                // 登录成功 {'res':1}
                if (data.res == 0){
                    $('#username').next().html('用户名或密码错误').show()
                }
                else
                {
                    // 跳转页面
                    location.href = data.next_url // /user/
                }
            })
        })
    })
</script>
{% endblock topfiles %}
{% block header_con %}{% endblock header_con %}
{% block search_bar %}{% endblock search_bar %}
{% block body %}
    <div class="login_top clearfix">
        <a href="index.html" class="login_logo"><img src="{% static 'images/logo.png' %}" style="width: 160px; height: 53px;"></a>
    </div>

    <div class="login_form_bg">
        <div class="login_form_wrap clearfix">
            <div class="login_banner fl"></div>
            <div class="slogan fl">学计算机 · 来尚硅谷</div>
            <div class="login_form fr">
                <div class="login_title clearfix">
                    <h1>用户登录</h1>
                    <a href="#">立即注册</a>
                </div>
                <div class="form_input">
                    {% csrf_token %}
                    <input type="text" id="username" class="name_input" value="{{ username }}" placeholder="请输入用户名">
                    <div class="user_error">输入错误</div>
                    <input type="password" id="pwd" class="pass_input" placeholder="请输入密码">
                    <div class="pwd_error">输入错误</div>
                    <div class="more_input clearfix">
                        <input type="checkbox" name="remember" {{ checked }}>
                        <label>记住用户名</label>
                        <a href="#">忘记密码</a>
                    </div>
                    <input type="button" id="btnLogin" value="登录" class="input_submit">
                </div>
            </div>
        </div>
    </div>
{% endblock body %}
```
改写index.html
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书店-首页{% endblock title %}
{% block topfiles %}
{% endblock topfiles %}
{% block body %}

    <div class="navbar_con">
        <div class="navbar">
            <h1 class="fl">全部商品分类</h1>
            <ul class="navlist fl">
                <li><a href="">首页</a></li>
                <li class="interval">|</li>
                <li><a href="">移动端书城</a></li>
                <li class="interval">|</li>
                <li><a href="">秒杀</a></li>
            </ul>
        </div>
    </div>

    <div class="center_con clearfix">
        <ul class="subnav fl">
            <li><a href="#model01" class="python">Python</a></li>
            <li><a href="#model02" class="javascript">Javascript</a></li>
            <li><a href="#model03" class="algorithms">数据结构与算法</a></li>
            <li><a href="#model04" class="machinelearning">机器学习</a></li>
            <li><a href="#model05" class="operatingsystem">操作系统</a></li>
            <li><a href="#model06" class="database">数据库</a></li>
        </ul>
        <div class="slide fl">
            <ul class="slide_pics">
                <li><img src="{% static 'images/slide.jpg' %}" alt="幻灯片" style="width: 760px; height: 270px;"></li>
                <li><img src="{% static 'images/slide02.jpg' %}" alt="幻灯片" style="width: 760px; height: 270px;"></li>
                <li><img src="{% static 'images/slide03.jpg' %}" alt="幻灯片" style="width: 760px; height: 270px;"></li>
                <li><img src="{% static 'images/slide04.jpg' %}" alt="幻灯片" style="width: 760px; height: 270px;"></li>
            </ul>
            <div class="prev"></div>
            <div class="next"></div>
            <ul class="points"></ul>
        </div>
        <div class="adv fl">
            <a href="#"><img src="{% static 'images/adv01.jpg' %}" style="width: 240px; height: 135px;"></a>
            <a href="#"><img src="{% static 'images/adv02.jpg' %}" style="width: 240px; height: 135px;"></a>
        </div>
    </div>

    <div class="list_model">
        <div class="list_title clearfix">
            <h3 class="fl" id="model01">Python</h3>
            <div class="subtitle fl">
                <span>|</span>
                {% for book in python_new %}
                    <a href="{% url 'books:detail' books_id=book.id %}">{{ book.name }}</a>
                {% endfor %}
            </div>
            <a href="#" class="book_more fr">查看更多 ></a>
        </div>

        <div class="book_con clearfix">
            <div class="book_banner fl"><img src="{% static 'images/banner01.jpg' %}"></div>
            <ul class="book_list fl">
                {% for book in python_hot %}
                <li>
                    <h4><a href="{% url 'books:detail' books_id=book.id  %}">{{ book.name }}</a></h4>
                    <a href="{% url 'books:detail' books_id=book.id  %}"><img src="{% static book.image %}"></a>
                    <div class="price">¥ {{ book.price }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>

    <div class="list_model">
        <div class="list_title clearfix">
            <h3 class="fl" id="model02">Javascript</h3>
            <div class="subtitle fl">
                <span>|</span>
                {% for book in javascript_new %}
                    <a href="#">{{ book.name }}</a>
                {% endfor %}
            </div>
            <a href="#" class="book_more fr">查看更多 ></a>
        </div>

        <div class="book_con clearfix">
            <div class="book_banner fl"><img src="{% static 'images/banner02.jpg' %}"></div>
            <ul class="book_list fl">
                {% for book in javascript_hot %}
                <li>
                    <h4><a href="#">{{ book.name }}</a></h4>
                    <a href="#"><img src="{% static book.image %}"></a>
                    <div class="price">¥ {{ book.price }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>

    <div class="list_model">
        <div class="list_title clearfix">
            <h3 class="fl" id="model03">数据结构与算法</h3>
            <div class="subtitle fl">
                <span>|</span>
                {% for book in algorithms_new %}
                    <a href="#">{{ book.name }}</a>
                {% endfor %}
            </div>
            <a href="#" class="book_more fr">查看更多 ></a>
        </div>

        <div class="book_con clearfix">
            <div class="book_banner fl"><img src="{% static 'images/banner03.jpg' %}"></div>
            <ul class="book_list fl">
                {% for book in algorithms_hot %}
                <li>
                    <h4><a href="#">{{ book.name }}</a></h4>
                    <a href="#"><img src="{% static book.image %}"></a>
                    <div class="price">¥ {{ book.price }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>

    <div class="list_model">
        <div class="list_title clearfix">
            <h3 class="fl" id="model04">机器学习</h3>
            <div class="subtitle fl">
                <span>|</span>
                {% for book in machinelearning_new %}
                    <a href="#">{{ book.name }}</a>
                {% endfor %}
            </div>
            <a href="#" class="book_more fr">查看更多 ></a>
        </div>

        <div class="book_con clearfix">
            <div class="book_banner fl"><img src="{% static 'images/banner04.jpg' %}"></div>
            <ul class="book_list fl">
                {% for book in machinelearning_hot %}
                <li>
                    <h4><a href="#">{{ book.name }}</a></h4>
                    <a href="#"><img src="{% static book.image %}"></a>
                    <div class="price">¥ {{ book.price }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>

    <div class="list_model">
        <div class="list_title clearfix">
            <h3 class="fl" id="model05">操作系统</h3>
            <div class="subtitle fl">
                <span>|</span>
                {% for book in operatingsystem_new %}
                    <a href="#">{{ book.name }}</a>
                {% endfor %}
            </div>
            <a href="#" class="book_more fr">查看更多 ></a>
        </div>

        <div class="book_con clearfix">
            <div class="book_banner fl"><img src="{% static 'images/banner05.jpg' %}"></div>
            <ul class="book_list fl">
                {% for book in operatingsystem_hot %}
                <li>
                    <h4><a href="#">{{ book.name }}</a></h4>
                    <a href="#"><img src="{% static book.image %}"></a>
                    <div class="price">¥ {{ book.price }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>

    <div class="list_model">
        <div class="list_title clearfix">
            <h3 class="fl" id="model06">数据库</h3>
            <div class="subtitle fl">
                <span>|</span>
                {% for book in database_new %}
                    <a href="#">{{ book.name }}</a>
                {% endfor %}
            </div>
            <a href="#" class="book_more fr">查看更多 ></a>
        </div>

        <div class="book_con clearfix">
            <div class="book_banner fl"><img src="{% static 'images/banner06.jpg' %}"></div>
            <ul class="book_list fl">
                {% for book in database_hot %}
                <li>
                    <h4><a href="#">{{ book.name }}</a></h4>
                    <a href="#"><img src="{% static book.image %}"></a>
                    <div class="price">¥ {{ book.price }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>

{% endblock body %}
```
改写detail.html
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书店-首页{% endblock title %}
{% block body %}
    <div class="navbar_con">
        <div class="navbar clearfix">
            <div class="subnav_con fl">
                <h1>全部商品分类</h1> 
                <span></span>           
                <ul class="subnav">
                    <li><a href="#" class="python">Python</a></li>
                    <li><a href="#" class="javascript">Javascript</a></li>
                    <li><a href="#" class="algorithms">数据结构与算法</a></li>
                    <li><a href="#" class="machinelearning">机器学习</a></li>
                    <li><a href="#" class="operatingsystem">操作系统</a></li>
                    <li><a href="#" class="database">数据库</a></li>
                </ul>
            </div>
            <ul class="navlist fl">
                <li><a href="">首页</a></li>
                <li class="interval">|</li>
                <li><a href="">移动端书城</a></li>
                <li class="interval">|</li>
                <li><a href="">秒杀</a></li>
            </ul>
        </div>
    </div>

    <div class="breadcrumb">
        <a href="#">全部分类</a>
        <span>></span>
        <a href="#">Python</a>
        <span>></span>
        <a href="#">商品详情</a>
    </div>

    <div class="book_detail_con clearfix">
        <div class="book_detail_pic fl"><img src="{% static books.image %}"></div>

        <div class="book_detail_list fr">
            <h3>{{ books.name }}</h3>
            <p>{{ books.desc }}</p>
            <div class="price_bar">
                <span class="show_pirze">¥<em>{{ books.price }}</em></span>
                <span class="show_unit">单  位：{{ books.unit }}</span>
            </div>
            <div class="book_num clearfix">
                <div class="num_name fl">数 量：</div>
                <div class="num_add fl">
                    <input type="text" class="num_show fl" value="1">
                    <a href="javascript:;" class="add fr">+</a>
                    <a href="javascript:;" class="minus fr">-</a>   
                </div> 
            </div>
            <div class="total">总价：<em>100元</em></div>
            <div class="operate_btn">
                <a href="javascript:;" class="buy_btn">立即购买</a>
                <a href="javascript:;" class="add_cart" id="add_cart">加入购物车</a>             
            </div>
        </div>
    </div>

    <div class="main_wrap clearfix">
        <div class="l_wrap fl clearfix">
            <div class="new_book">
                <h3>新品推荐</h3>
                <ul>
                    {% for book in books_li %}
                    <li>
                        <a href="{% url 'books:detail' books_id=books.id %}"><img src="{% static book.image %}"></a>
                        <h4><a href="{% url 'books:detail' books_id=books.id %}">{{ book.name }}</a></h4>
                        <div class="price">￥{{ book.price }}</div>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>

        <div class="r_wrap fr clearfix">
            <ul class="detail_tab clearfix">
                <li class="active">商品介绍</li>
                <li>评论</li>
            </ul>

            <div class="tab_content">
                <dl>
                    <dt>商品详情：</dt>
                    <dd>{{ books.detail | safe }}</dd>
                </dl>
            </div>

        </div>
    </div>
    <div class="add_jump"></div>
{% endblock body %}
```
这里要注意的是override也就是复写的问题，其实是面向对象的思想。

## 9，列表页的开发

接下来我们来实现列表页。通过观察list.html我们可以发现，这里有分页的功能，以及按照不同特征来进行排序，比如价格，比如人气这样的特征。这里要注意分页功能的实现，以及为什么要分页，一下读取所有数据，数据库的压力很大。
```py
# 商品种类 页码 排序方式
# /list/(种类id)/(页码)/?sort=排序方式
from django.core.paginator import Paginator

def list(request, type_id, page):
    '''商品列表页面'''
    # 获取排序方式
    sort = request.GET.get('sort', 'default')

    # 判断type_id是否合法
    if int(type_id) not in BOOKS_TYPE.keys():
        return redirect(reverse('books:index'))

    # 根据商品种类id和排序方式查询数据
    books_li = Books.objects.get_books_by_type(type_id=type_id, sort=sort)

    # 分页
    paginator = Paginator(books_li, 1)

    # 获取分页之后的总页数
    num_pages = paginator.num_pages

    # 取第page页数据
    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)

    # 返回值是一个Page类的实例对象
    books_li = paginator.page(page)

    # 进行页码控制
    # 1.总页数<5, 显示所有页码
    # 2.当前页是前3页，显示1-5页
    # 3.当前页是后3页，显示后5页 10 9 8 7
    # 4.其他情况，显示当前页前2页，后2页，当前页
    if num_pages < 5:
        pages = range(1, num_pages+1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages-4, num_pages+1)
    else:
        pages = range(page-2, page+3)

    # 新品推荐
    books_new = Books.objects.get_books_by_type(type_id=type_id, limit=2, sort='new')

    # 定义上下文
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
```
然后配置urls.py
```py
# books/urls.py
url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)/$', views.list, name='list'), # 列表页
```
将list.html拷贝到templates/books
先继承base.html。
将index.html首页里面的查看更多，修改url定向。
```py
{% url 'books:list' type_id=1 page=1 %}
```
修改名称。
```
{{ type_title }}
```
新品推荐。
```html
{% for book in books_new %}
<li>
    <a href="{% url 'books:detail' books_id=book.id %}"><img src="{% static book.image %}"></a>
    <h4><a href="{% url 'books:detail' books_id=book.id %}">{{ book.name }}</a></h4>
    <div class="price">￥{{ book.price }}</div>
</li>
{% endfor %}
```
按不同的特征排序。
```html
<a href="/list/{{ type_id }}/1/" {% if sort == 'default' %}class="active"{% endif %}>默认</a>
<a href="/list/{{ type_id }}/1/?sort=price" {% if sort == 'price' %}class="active"{% endif %}>价格</a>
<a href="/list/{{ type_id }}/1/?sort=hot" {% if sort == 'hot' %}class="active"{% endif %}>人气</a>
```
商品列表
```html
{% for books in books_li %}
    <li>
        <a href="{% url 'books:detail' books_id=books.id %}"><img src="{% static books.image %}"></a>
        <h4><a href="{% url 'books:detail' books_id=books.id %}">{{ books.name }}</a></h4>
        <div class="operate">
            <span class="price">￥{{ books.price }}</span>
            <span class="unit">{{ books.unit }}</span>
            <a href="#" class="add_books" title="加入购物车"></a>
        </div>
    </li>
{% endfor %}
```
前端分页功能的实现。
```html
{% if books_li.has_previous %}
    <a href="/list/{{ type_id }}/{{ books_li.previous_page_number }}/?sort={{ sort }}"><上一页</a>
{% endif %}
{% for pindex in pages %}
    {% if pindex == books_li.number %}
        <a href="/list/{{ type_id }}/{{ pindex }}/?sort={{ sort }}" class="active">{{ pindex }}</a>
    {% else %}
        <a href="/list/{{ type_id }}/{{ pindex }}/?sort={{ sort }}">{{ pindex }}</a>
    {% endif %}
{% endfor %}
{% if books_li.has_next %}
    <a href="/list/{{ type_id }}/{{ books_li.next_page_number }}/?sort={{ sort }}">下一页></a>
{% endif %}
```

# <a id="4">4，用户中心的实现</a>
接下来我们来实现用户中心的功能，先不实现最近浏览这个功能。首先来看一下这个前端页面，那我们知道我们还得给User这个model添加地址表。
那我们先来建model
```py
# user/models.py

class Address(BaseModel):
    '''地址模型类'''
    recipient_name = models.CharField(max_length=20, verbose_name='收件人')
    recipient_addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮政编码')
    recipient_phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    passport = models.ForeignKey('Passport', verbose_name='账户')

    objects = AddressManager()

    class Meta:
        db_table = 's_user_address'
```
然后实现AddressManager()，对一些常用函数做抽象。
```python
class AddressManager(models.Manager):
    '''地址模型管理器类'''
    def get_default_address(self, passport_id):
        '''查询指定用户的默认收货地址'''
        try:
            addr = self.get(passport_id=passport_id, is_default=True)
        except self.model.DoesNotExist:
            # 没有默认收货地址
            addr = None
        return addr

    def add_one_address(self, passport_id, recipient_name, recipient_addr, zip_code, recipient_phone):
        '''添加收货地址'''
        # 判断用户是否有默认收货地址
        addr = self.get_default_address(passport_id=passport_id)

        if addr:
            # 存在默认地址
            is_default = False
        else:
            # 不存在默认地址
            is_default = True

        # 添加一个地址
        addr = self.create(passport_id=passport_id,
                           recipient_name=recipient_name,
                           recipient_addr=recipient_addr,
                           zip_code=zip_code,
                           recipient_phone=recipient_phone,
                           is_default=is_default)
        return addr
```
进行数据库迁移
```
$ python manage.py makemigrations users
$ python manage.py migrate
```
然后编写视图函数views.py
```py
def user(request):
    '''用户中心-信息页'''
    passport_id = request.session.get('passport_id')
    # 获取用户的基本信息
    addr = Address.objects.get_default_address(passport_id=passport_id)

    books_li = []

    context = {
        'addr': addr,
        'page': 'user',
        'books_li': books_li
    }

    return render(request, 'users/user_center_info.html', context)
```
配置urls.py
```
url(r'^$', views.user, name='user'), # 用户中心-信息页
```
然后将user_center_info.html拷贝到templates/users文件夹下。
还是继承base.html，然后对模板进行渲染。
```html
<li><span>用户名：</span>{{ request.session.username }}</li>
{% if addr %}
    <li><span>联系方式：</span>{{ addr.recipient_phone }}</li>
    <li><span>联系地址：</span>{{ addr.recipient_addr }}</li>
{% else %}
    <li><span>联系方式：</span>无</li>
    <li><span>联系地址：</span>无</li>
{% endif %}
```
我们这里思考一下，用户中心必须登录以后才可以使用，我们应该怎么实现这个功能呢？
在这里，python的装饰器功能就派上用场了。
新建一个utils文件夹，用来存放自己编写的一些常用功能函数。
```py
# utils/decorators.py
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def login_required(view_func):
    '''登录判断装饰器'''
    def wrapper(request, *view_args, **view_kwargs):
        if request.session.has_key('islogin'):
            # 用户已登录
            return view_func(request, *view_args, **view_kwargs)
        else:
            # 跳转到登录页面
            return redirect(reverse('user:login'))
    return wrapper
```
然后把这个装饰器打在views.py里的user函数上面。
```
@login_required
```
装饰器有很多作用，比如可以限定具有某些权限的用户才能登陆，等等。

# <a id="5">5，购物车功能</a>
## 1，创建models
这里我们要引进redis的使用。大家可以参考《redis实战》这本书，有很多redis的妙用，网上有电子版。
我们使用redis实现购物车的功能。因为购物车里的数据相对不是那么重要，而且更新频繁。当然如果要是考虑到安全性，还是要持久化到数据库中比较好。redis在内存中不是很安全，比如之前redis就被攻击过。
使用shell命令
```
ps -ef | grep redis
```
来检查redis server是否启动。
我们现在配置文件中配置缓存有关的东西。
```py
# settings.py
# pip install django-redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": ""
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```
然后新建一个购物车cart app。
```
$ python manage.py startapp cart
```
然后开始编写视图函数。先来编写向购物车中添加商品的功能。
```py
# cart/views.py
from django.shortcuts import render
from django.http import JsonResponse
from books.models import Books
from utils.decorators import login_required
from django_redis import get_redis_connection
# Create your views here.


# 前端发过来的数据：商品id 商品数目 books_id books_count
# 涉及到数据的修改，使用post方式

@login_required
def cart_add(request):
    '''向购物车中添加数据'''

    # 接收数据
    books_id = request.POST.get('books_id')
    books_count = request.POST.get('books_count')

    # 进行数据校验
    if not all([books_id, books_count]):
        return JsonResponse({'res':1 , 'errmsg':'数据不完整'})

    books = Books.objects.get_books_by_id(books_id=books_id)
    if books is None:
        # 商品不存在
        return JsonResponse({'res':2, 'errmsg':'商品不存在'})

    try:
        count = int(books_count)
    except Exception as e:
        # 商品数目不合法
        return JsonResponse({'res':3, 'errmsg':'商品数量必须为数字'})

    # 添加商品到购物车
    # 每个用户的购物车记录用一条hash数据保存，格式:cart_用户id: 商品id 商品数量
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')

    res = conn.hget(cart_key, books_id)
    if res is None:
        # 如果用户的购车中没有添加过该商品，则添加数据
        res = count
    else:
        # 如果用户的购车中已经添加过该商品，则累计商品数目
        res = int(res) + count

    # 判断商品的库存
    if res > books.stock:
        # 库存不足
        return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
    else:
        conn.hset(cart_key, books_id, res)

    # 返回结果
    return JsonResponse({'res': 5})
```
将商品添加到购物车的功能就实现了。

## 2，渲染购物车页面
在登陆以后，我们应该能够看到购物车里的商品数量，现在我们就来实现这个功能。
```py
# cart/views.py

@login_required
def cart_count(request):
    '''获取用户购物车中商品的数目'''

    # 计算用户购物车商品的数量
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')
    # res = conn.hlen(cart_key) 显示商品的条目数
    res = 0
    res_list = conn.hvals(cart_key)

    for i in res_list:
        res += int(i)

    # 返回结果
    return JsonResponse({'res': res})
```
然后在前端页面调用这个接口，并渲染出来。
在base.html中添加：
```html
# base.html
    {# 获取用户购物车中商品的数目 #}
    {% block cart_count %}
        <script>
            $.get('/cart/count/', function (data) {
                // {'res':商品的总数}
                $('#show_count').html(data.res)
            })
        </script>
    {% endblock cart_count %}
```
而在登陆和注册页面，不需要显示这个，所以我们override掉这个块。
```html
{% block cart_count %}{% endblock cart_count %}
```
然后配置urls.py
```
    url(r'^add/$', views.cart_add, name='add'), # 添加购物车数据
    url(r'^count/$', views.cart_count, name='count'), # 获取用户购物车中商品的数量
```
然后在根目录urls.py中配置url
```
    url(r'^cart/', include('cart.urls', namespace='cart')), # 购物车模块
```
然后在前端详情页`detail.html`编写添加到购物车的jquery代码。
```html

<script type="text/javascript">
    $('#add_cart').click(function(){
        // 获取商品的id和商品数量
        var books_id = $(this).attr('books_id');
        var books_count = $('.num_show').val();
        var csrf = $('input[name="csrfmiddlewaretoken"]').val();
        // 发起请求，访问/cart/add/, 进行购物车数据的添加
        var params = {
            'books_id': books_id,
            'books_count': books_count,
            'csrfmiddlewaretoken': csrf
        }

        $.post('/cart/add/', params, function (data) {
            if (data.res == 5){
                // 添加成功
                var count = $('#show_count').html();
                var count = parseInt(count) + parseInt(books_count);
                $('#show_count').html(count);
            } else {
                // 添加失败
                alert(data.errmsg)
            }
        })
    })
</script>
```
发送ajax post请求来更新购物车数量。
再改写html tag。
```
{% csrf_token %}
<a href="javascript:;" class="buy_btn">立即购买</a>
<a href="javascript:;" books_id="{{ books.id }}" class="add_cart" id="add_cart">加入购物车</a>
```
现在我们可以将商品添加到购物车中去了。
然后我们再编写一段jquery代码，实现+/-商品数量的功能。并且可以自动更新总价格。
```html
// detail.html
{% block topfiles %}
<script>
$(function () {
    update_total_price()
    // 计算总价
    function update_total_price() {
        // 获取商品的价格和数量
        books_price = $('.show_pirze').children('em').text()
        books_count = $('.num_show').val()
        // 计算商品的总价
        books_price = parseFloat(books_price)
        books_count = parseInt(books_count)
        total_price = books_price * books_count
        // 设置商品总价
        $('.total').children('em').text(total_price.toFixed(2) + '元')
    }

    // 商品增加
    $('.add').click(function () {
        // 获取商品的数量
        books_count = $('.num_show').val()
        // 加1
        books_count = parseInt(books_count) + 1
        // 重新设置值
        $('.num_show').val(books_count)
        // 计算总价
        update_total_price()
    })

    // 商品减少
    $('.minus').click(function () {
        // 获取商品的数量
        books_count = $('.num_show').val()
        // 加1
        books_count = parseInt(books_count) - 1
        if (books_count == 0){
            books_count = 1
        }
        // 重新设置值
        $('.num_show').val(books_count)
        // 计算总价
        update_total_price()
    })

    // 手动输入
    $('.num_show').blur(function () {
        // 获取商品的数量
        books_count = $(this).val()
        // 数据校验
        if (isNaN(books_count) || books_count.trim().length == 0 || parseInt(books_count) <= 0 ){
            books_count = 1
        }
        // 重新设置值
        $('.num_show').val(parseInt(books_count))
        // 计算总价
        update_total_price()
    })
})
</script>
{% endblock topfiles %}
```
好，添加商品到购物车的功能我们就实现好了。

## 3，购物车页面的开发
接下来我们来实现展示购物车页面的功能。
编写views.py。
```py
# cart/views.py

@login_required
def cart_show(request):
    '''显示用户购物车页面'''
    passport_id = request.session.get('passport_id')
    # 获取用户购物车的记录
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % passport_id
    res_dict = conn.hgetall(cart_key)

    books_li = []
    # 保存所有商品的总数
    total_count = 0
    # 保存所有商品的总价格
    total_price = 0

    # 遍历res_dict获取商品的数据
    for id, count in res_dict.items():
        # 根据id获取商品的信息
        books = Books.objects.get_books_by_id(books_id=id)
        # 保存商品的数目
        books.count = count
        # 保存商品的小计
        books.amount = int(count) * books.price
        # books_li.append((books, count))
        books_li.append(books)

        total_count += int(count)
        total_price += int(count) * books.price

    # 定义模板上下文
    context = {
        'books_li': books_li,
        'total_count': total_count,
        'total_price': total_price,
    }

    return render(request, 'cart/cart.html', context)
```
然后配置urls.py
```
    url(r'^$', views.cart_show, name='show'), # 显示用户的购物车页面
```
然后将cart.html拷贝到templates/cart文件夹下面。
还是继承base.html。然后在base.html中改写url定向。
```
{% url 'cart:show' %}
```
接下来，我们把订单列表渲染出来。
```html
    {% for book in books_li %}
    <ul class="cart_list_td clearfix">
        {# 提交表单时，如果checkbox没有被选中，它的值不会被提交 #}
        <li class="col01"><input type="checkbox" name="books_ids" value="{{ book.id }}" checked></li>
        <li class="col02"><img src="{% static book.image %}"></li>
        <li class="col03">{{ book.name }}<br><em>{{ book.price }}元/{{ book.unit }}</em></li>
        <li class="col04">{{ book.unit }}</li>
        <li class="col05">{{ book.price }}</li>
        <li class="col06">
            <div class="num_add">
                <a href="javascript:;" class="add fl">+</a>
                <input type="text" books_id="{{ book.id }}" class="num_show fl" value="{{ book.count }}">
                <a href="javascript:;" class="minus fl">-</a>   
            </div>
        </li>
        <li class="col07">{{ book.amount }}元</li>
        <li class="col08"><a href="javascript:;">删除</a></li>
    </ul>
    {% endfor %}
```

## 4，购物车中删除商品的功能
先来编写views.py函数。
```py
# cart/views.py
# 前端传过来的参数:商品id books_id
# post
# /cart/del/

@login_required
def cart_del(request):
    '''删除用户购物车中商品的信息'''

    # 接收数据
    books_id = request.POST.get('books_id')

    # 校验商品是否存放
    if not all([books_id]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

    books = Books.objects.get_books_by_id(books_id=books_id)
    if books is None:
        return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

    # 删除购物车商品信息
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')
    conn.hdel(cart_key, books_id)

    # 返回信息
    return JsonResponse({'res': 3})
```
配置urls.py
```
url(r'^del/$', views.cart_del, name='delete'), # 购物车商品记录删除
```
然后在购物车页面cart.html编写jquery代码来调用del接口。
```js
{% block topfiles %}
    <script>
    $(function () {
        update_cart_count()
        // 计算所有被选中商品的总价，总数目和商品的小计
        function update_total_price() {
            total_count = 0
            total_price = 0
            // 获取所有被选中的商品所在的ul元素
            $('.cart_list_td').find(':checked').parents('ul').each(function () {
                // 计算商品的小计
                res_dict = update_books_price($(this))

                total_count += res_dict.books_count
                total_price += res_dict.books_amount
            })

            // 设置商品的总价和总数目
            $('.settlements').find('em').text(total_price.toFixed(2))
            $('.settlements').find('b').text(total_count)
        }

        // 计算商品的小计
        function update_books_price(books_ul) {
            // 获取每一个商品的价格和数量
                books_price = books_ul.children('.col05').text()
                books_count = books_ul.find('.num_show').val()

                // 计算商品的小计
                books_price = parseFloat(books_price)
                books_count = parseInt(books_count)
                books_amount = books_price * books_count

                // 设置商品的小计
                books_ul.children('.col07').text(books_amount.toFixed(2) + '元')

                return {
                    'books_count': books_count,
                    'books_amount': books_amount
                }
        }


        // 更新页面上购物车商品的总数
        function update_cart_count() {
            #  更新列表上方商品总数
            $.get('/cart/count/', function (data) {
                $('.total_count').children('em').text(data.res)
            #  更新页面右上方购物车商品总数
            $.get('/cart/count/', function (data) {
                $('#show_count').html(data.res)
            })
        }

        // 购物车商品信息的删除
        $('.cart_list_td').children('.col08').children('a').click(function () {
            // 获取删除的商品的id
            books_ul = $(this).parents('ul')
            books_id = books_ul.find('.num_show').attr('books_id')
            csrf = $('input[name="csrfmiddlewaretoken"]').val()
            params = {
                "books_id": books_id,
                "csrfmiddlewaretoken": csrf
            }
            // 发起ajax请求，访问/cart/del/
            $.post('/cart/del/', params, function (data) {
                if (data.res == 3){
                    // 删除成功
                    // 移除商品对应的ul元素
                    books_ul.remove() // books.empty()
                    // 判断商品对应的checkbox是否选中
                    is_checked = books_ul.find(':checkbox').prop('checked')
                    if (is_checked){
                        update_total_price()
                    }
                    // 更新页面购物车商品总数
                    update_cart_count()
                    // 更新选择框状态
                    $('.settlements').find(":checkbox").prop('checked', false)
                }
            })
        })
    })
    </script>
{% endblock topfiles %}
```
为避免403，我们添加一行{% csrf_token %}

## 5，实现购物车页面编辑商品数量的功能。
我们先来编写更新购物车的接口。
```python
# cart/views.py
# 前端传过来的参数:商品id books_id 更新数目 books_count
# post
# /cart/update/

@login_required
def cart_update(request):
    '''更新购物车商品数目'''

    # 接收数据
    books_id = request.POST.get('books_id')
    books_count = request.POST.get('books_count')

    # 数据的校验
    if not all([books_id, books_count]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

    books = Books.objects.get_books_by_id(books_id=books_id)
    if books is None:
        return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

    try:
        books_count = int(books_count)
    except Exception as e:
        return JsonResponse({'res': 3, 'errmsg': '商品数目必须为数字'})

    # 更新操作
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')

    # 判断商品库存
    if books_count > books.stock:
        return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

    conn.hset(cart_key, books_id, books_count)

    return JsonResponse({'res': 5})
```

注意别忘了配置cart app的urls.py。
```python
url(r'^update/$', views.cart_update, name="update")
```
然后编写jquery代码来实现前端更新数量以及全选这样的功能。

```javascript
        // 全选和全不选
        $('.settlements').find(':checkbox').change(function () {
            // 获取全选checkbox的选中状态
            is_checked = $(this).prop('checked')

            // 遍历所有商品对应的checkbox,设置checked属性和全选checkbox一致
            $('.cart_list_td').find(':checkbox').each(function () {
                $(this).prop('checked', is_checked)
            })

            // 更新商品的信息
            update_total_price()
        })

        // 商品对应的checkbox状态发生改变时，全选checkbox的改变
        $('.cart_list_td').find(':checkbox').change(function () {
            // 获取所有商品对应的checkbox的数目
            all_len = $('.cart_list_td').find(':checkbox').length
            // 获取所有被选中商品的checkbox的数目
            checked_len  = $('.cart_list_td').find(':checked').length

            if (checked_len < all_len){
                $('.settlements').find(':checkbox').prop('checked', false)
            }
            else {
                 $('.settlements').find(':checkbox').prop('checked', true)
            }

            // 更新商品的信息
            update_total_price()
        })
        // 购物车商品数目的增加
        $('.add').click(function () {
            // 获取商品的数目和商品的id
            books_count = $(this).next().val()
            books_id = $(this).next().attr('books_id')

            // 更新购物车信息
            books_count = parseInt(books_count) + 1
            update_remote_cart_info(books_id, books_count)

            // 根据更新的结果进行操作
            if (error_update == false){
                // 更新成功
                $(this).next().val(books_count)
                // 获取商品对应的checkbox的选中状态
                is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
                if (is_checked){
                    // 更新商品的总数目，总价格和小计
                    update_total_price()
                }
                else{
                    // 更新商品的小计
                    update_books_price($(this).parents('ul'))
                }
                // 更新页面购物车商品总数
                update_cart_count()
            }
        })

        // 购物车商品数目的减少
        $('.minus').click(function () {
            // 获取商品的数目和商品的id
            books_count = $(this).prev().val()
            books_id = $(this).prev().attr('books_id')

            // 更新购物车信息
            books_count = parseInt(books_count) - 1
            if (books_count <= 0){
                books_count = 1

            }

            update_remote_cart_info(books_id, books_count)

            // 根据更新的结果进行操作
            if (error_update == false){
                // 更新成功
                $(this).prev().val(books_count)
                // 获取商品对应的checkbox的选中状态
                is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
                if (is_checked){
                    // 更新商品的总数目，总价格和小计
                    update_total_price()
                }
                else{
                    // 更新商品的小计
                    update_books_price($(this).parents('ul'))
                }
                // 更新页面购物车商品总数
                update_cart_count()
            }
        })

        pre_books_count = 0
        $('.num_show').focus(function () {
            pre_books_count = $(this).val()
        })

         // 购物车商品数目的手动输入
        $('.num_show').blur(function () {
            // 获取商品的数目和商品的id
            books_count = $(this).val()
            books_id = $(this).attr('books_id')

            // 校验用户输入的商品数目
            if (isNaN(books_count) || books_count.trim().length == 0 || parseInt(books_count)<=0){
                // 设置回输入之前的值
                $(this).val(pre_books_count)
                return
            }

            // 更新购物车信息
            books_count = parseInt(books_count)

            update_remote_cart_info(books_id, books_count)

            // 根据更新的结果进行操作
            if (error_update == false){
                // 更新成功
                $(this).val(books_count)
                // 获取商品对应的checkbox的选中状态
                is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
                if (is_checked){
                    // 更新商品的总数目，总价格和小计
                    update_total_price()
                }
                else{
                    // 更新商品的小计
                    update_books_price($(this).parents('ul'))
                }
                // 更新页面购物车商品总数
                update_cart_count()
            }
            else{
                // 设置回输入之前的值
                $(this).val(pre_books_count)
            }
        })
```
这里要注意看看jquery是怎么发送ajax post请求的。
```js
        // 更新redis中购物车商品数目
        error_update = false
        function update_remote_cart_info(books_id, books_count) {
            csrf = $('input[name="csrfmiddlewaretoken"]').val()
            params = {
                'books_id': books_id,
                'books_count': books_count,
                'csrfmiddlewaretoken': csrf
            }
            // 设置同步
            $.ajaxSettings.async = false
            // 发起请求，访问/cart/update/
            $.post('/cart/update/', params, function (data) {
                if (data.res == 5){
                    // alert('更新成功')
                    error_update = false
                }
                else {
                    error_update = true
                    alert(data.errmsg)
                }
            })
            // 设置异步
            $.ajaxSettings.async = true
        }
```
这里设置了同步，因为我们需要马上更新购物车数据，即使阻塞了其他操作也在所不惜。
好，购物车页面基本就开发完了。

# <a id="6">6，订单页面的开发</a>
## 1，创建models
先来设计数据库表结构，记住表结构的设计是最重要的，因为一般情况下设计好表结构，就不再变更了。
我们先安装order app。
```
$ python manage.py startapp order
```
然后订单信息model的设计如下：

```python
from django.db import models
from db.base_model import BaseModel
# Create your models here.

class OrderInfo(BaseModel):
    '''订单信息模型类'''

    PAY_METHOD_CHOICES = (
        (1, "货到付款"),
        (2, "微信支付"),
        (3, "支付宝"),
        (4, "银联支付")
    )

    PAY_METHODS_ENUM = {
        "CASH": 1,
        "WEIXIN": 2,
        "ALIPAY": 3,
        "UNIONPAY": 4,
    }

    ORDER_STATUS_CHOICES = (
        (1, "待支付"),
        (2, "待发货"),
        (3, "待收货"),
        (4, "待评价"),
        (5, "已完成"),
    )

    order_id = models.CharField(max_length=64, primary_key=True, verbose_name='订单编号')
    passport = models.ForeignKey('users.Passport', verbose_name='下单账户')
    addr = models.ForeignKey('users.Address', verbose_name='收货地址')
    total_count = models.IntegerField(default=1, verbose_name='商品总数')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单运费')
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name='支付方式')
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='订单状态')
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='支付编号')

    class Meta:
        db_table = 's_order_info'
```
由于每一笔订单都是由不同的商品组成，所以我们需要把一笔订单拆分开，来建立一个订单中每种商品的信息数据表。关系数据库的一个好处就是强约束，冗余也很少，这点比mongodb好。
```py
class OrderGoods(BaseModel):
    '''订单商品模型类'''
    order = models.ForeignKey('OrderInfo', verbose_name='所属订单')
    books = models.ForeignKey('books.Books', verbose_name='订单商品')
    count = models.IntegerField(default=1, verbose_name='商品数量')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    # comment = models.CharField(max_length=128, null=True, blank=True, verbose_name='商品评论')

    class Meta:
        db_table = 's_order_books'
```
接下来我们来做数据库迁移。别忘了在settings.py中添加order app。
```
$ python manage.py makemigrations order
$ python manage.py migrate
```

## 2，开发有关订单的接口。
我们先把订单显示页面来渲染出来。
先来开发后台接口。
```python
from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from utils.decorators import login_required
from django.http import HttpResponse,JsonResponse
from users.models import Address
from books.models import Books
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from datetime import datetime
from django.conf import settings
import os
import time
# Create your views here.


@login_required
def order_place(request):
    '''显示提交订单页面'''
    # 接收数据
    books_ids = request.POST.getlist('books_ids')

    # 校验数据
    if not all(books_ids):
        # 跳转会购物车页面
        return redirect(reverse('cart:show'))

    # 用户收货地址
    passport_id = request.session.get('passport_id')
    addr = Address.objects.get_default_address(passport_id=passport_id)

    # 用户要购买商品的信息
    books_li = []
    # 商品的总数目和总金额
    total_count = 0
    total_price = 0

    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % passport_id

    for id in books_ids:
        # 根据id获取商品的信息
        books = Books.objects.get_books_by_id(books_id=id)
        # 从redis中获取用户要购买的商品的数目
        count = conn.hget(cart_key, id)
        books.count = count
        # 计算商品的小计
        amount = int(count) * books.price
        books.amount = amount
        books_li.append(books)

        # 累计计算商品的总数目和总金额
        total_count += int(count)
        total_price += books.amount

    # 商品运费和实付款
    transit_price = 10
    total_pay = total_price + transit_price

    # 1,2,3
    books_ids = ','.join(books_ids)
    # 组织模板上下文
    context = {
        'addr': addr,
        'books_li': books_li,
        'total_count': total_count,
        'total_price': total_price,
        'transit_price': transit_price,
        'total_pay': total_pay,
        'books_ids': books_ids,
    }

    # 使用模板
    return render(request, 'order/place_order.html', context)
```
然后配置urls.py。
```py
# urls.py
    url(r'^order/', include('order.urls', namespace='order')), # 订单模块
```
```py
# order/urls.py
from django.conf.urls import url
from order import views

urlpatterns = [
    url(r'^place/$', views.order_place, name='place'), # 订单提交页面
]
```
然后将place_order.html拷贝到templates/order文件夹下。并用继承base.html的方式来改写。
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书店-首页{% endblock title %}
{% block topfiles %}
{% endblock topfiles %}
{% block body %}
    
    <h3 class="common_title">确认收货地址</h3>

    <div class="common_list_con clearfix">
        <dl>
            <dt>寄送到：</dt>
            <dd><input type="radio" name="" checked="">北京市 海淀区 东北旺西路8号中关村软件园 （李思 收） 182****7528</dd>
        </dl>
        <a href="user_center_site.html" class="edit_site">编辑收货地址</a>

    </div>
    
    <h3 class="common_title">支付方式</h3>  
    <div class="common_list_con clearfix">
        <div class="pay_style_con clearfix">
            <input type="radio" name="pay_style" checked>
            <label class="cash">货到付款</label>
            <input type="radio" name="pay_style">
            <label class="weixin">微信支付</label>
            <input type="radio" name="pay_style">
            <label class="zhifubao"></label>
            <input type="radio" name="pay_style">
            <label class="bank">银行卡支付</label>
        </div>
    </div>

    <h3 class="common_title">商品列表</h3>
    
    <div class="common_list_con clearfix">
        <ul class="book_list_th clearfix">
            <li class="col01">商品名称</li>
            <li class="col02">商品单位</li>
            <li class="col03">商品价格</li>
            <li class="col04">数量</li>
            <li class="col05">小计</li>       
        </ul>
        <ul class="book_list_td clearfix">
            <li class="col01">1</li>            
            <li class="col02"><img src="images/book/book012.jpg"></li>
            <li class="col03">计算机程序设计艺术</li>
            <li class="col04">册</li>
            <li class="col05">25.80元</li>
            <li class="col06">1</li>
            <li class="col07">25.80元</li>   
        </ul>
        <ul class="book_list_td clearfix">
            <li class="col01">2</li>
            <li class="col02"><img src="images/book/book003.jpg"></li>
            <li class="col03">Python Cookbook</li>
            <li class="col04">册</li>
            <li class="col05">16.80元</li>
            <li class="col06">1</li>
            <li class="col07">16.80元</li>
        </ul>
    </div>

    <h3 class="common_title">总金额结算</h3>

    <div class="common_list_con clearfix">
        <div class="settle_con">
            <div class="total_book_count">共<em>2</em>件商品，总金额<b>42.60元</b></div>
            <div class="transit">运费：<b>10元</b></div>
            <div class="total_pay">实付款：<b>52.60元</b></div>
        </div>
    </div>

    <div class="order_submit clearfix">
        <a href="javascript:;" id="order_btn" books_ids="{{ books_ids }}">提交订单</a> 
    </div>
{% endblock body %}
{% block bottom %}
    <div class="popup_con">
        <div class="popup">
            <p>订单提交成功！</p>
        </div>
        <div class="mask"></div>
    </div>
{% endblock bottom %}
```

然后将模板中的对应元素修改为后端渲染的代码。

```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书店-我的订单{% endblock title %}
{% block topfiles %}
{% endblock topfiles %}
{% block body %}

    <h3 class="common_title">确认收货地址</h3>

    <div class="common_list_con clearfix">
        <dl>
            <dt>寄送到：</dt>
            <dd><input type="radio" name="addr_id" value="{{ addr.id }}" checked="">{{ addr.recipient_addr }} （{{ addr.recipient_name }} 收） {{ addr.recipient_phone }}</dd>
        </dl>
        <a href="user_center_site.html" class="edit_site">编辑收货地址</a>

    </div>

    <h3 class="common_title">支付方式</h3>
    <div class="common_list_con clearfix">
        <div class="pay_style_con clearfix">
            <input type="radio" name="pay_style" checked>
            <label class="cash">货到付款</label>
            <input type="radio" name="pay_style">
            <label class="weixin">微信支付</label>
            <input type="radio" name="pay_style">
            <label class="zhifubao"></label>
            <input type="radio" name="pay_style">
            <label class="bank">银行卡支付</label>
        </div>
    </div>

    <h3 class="common_title">商品列表</h3>
    <div class="common_list_con clearfix">
        <ul class="book_list_th clearfix">
            <li class="col01">商品名称</li>
            <li class="col02">商品单位</li>
            <li class="col03">商品价格</li>
            <li class="col04">数量</li>
            <li class="col05">小计</li>
        </ul>
        {% for book in books_li %}
        <ul class="books_list_td clearfix">
            <li class="col01">{{ forloop.counter }}</li>
            <li class="col02"><img src="{% static book.image %}"></li>
            <li class="col03">{{ book.name }}</li>
            <li class="col04">{{ book.unit }}</li>
            <li class="col05">{{ book.price }}元</li>
            <li class="col06">{{ book.count }}</li>
            <li class="col07">{{ book.amount }}元</li>
        </ul>
        {% endfor %}
    </div>

    <h3 class="common_title">总金额结算</h3>

    <div class="common_list_con clearfix">
        <div class="settle_con">
            <div class="total_book_count">共<em>{{ total_count }}</em>件商品，总金额<b>{{ total_price }}元</b></div>
            <div class="transit">运费：<b>{{ transit_price }}元</b></div>
            <div class="total_pay">实付款：<b>{{ total_pay }}元</b></div>
        </div>
    </div>

    <div class="order_submit clearfix">
        <a href="javascript:;" id="order_btn" books_ids="{{ books_ids }}">提交订单</a>
    </div>
{% endblock body %}
{% block bottom %}
    <div class="popup_con">
        <div class="popup">
            <p>订单提交成功！</p>
        </div>
        <div class="mask"></div>
    </div>
{% endblock bottom %}
```
那么订单显示页面就初步开发完了。

## 3，订单提交功能
接下来我们来开发提交订单的功能。先开发后端接口，这里要用到事务，transaction，原子操作的概念。

```python
# order/views.py
# 提交订单，需要向两张表中添加信息
# s_order_info:订单信息表 添加一条
# s_order_books: 订单商品表， 订单中买了几件商品，添加几条记录
# 前端需要提交过来的数据: 地址 支付方式 购买的商品id

# 1.向订单表中添加一条信息
# 2.遍历向订单商品表中添加信息
    # 2.1 添加订单商品信息之后，增加商品销量，减少库存
    # 2.2 累计计算订单商品的总数目和总金额
# 3.更新订单商品的总数目和总金额
# 4.清除购物车对应信息

# 事务:原子性:一组sql操作，要么都成功，要么都失败。
# 开启事务: begin;
# 事务回滚: rollback;
# 事务提交: commit;
# 设置保存点: savepoint 保存点;
# 回滚到保存点: rollback to 保存点;
from django.db import transaction

@transaction.atomic
def order_commit(request):
    '''生成订单'''
    # 验证用户是否登录
    if not request.session.has_key('islogin'):
        return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

    # 接收数据
    addr_id = request.POST.get('addr_id')
    pay_method = request.POST.get('pay_method')
    books_ids = request.POST.get('books_ids')

    # 进行数据校验
    if not all([addr_id, pay_method, books_ids]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

    try:
        addr = Address.objects.get(id=addr_id)
    except Exception as e:
        # 地址信息出错
        return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

    if int(pay_method) not in OrderInfo.PAY_METHODS_ENUM.values():
        return JsonResponse({'res': 3, 'errmsg': '不支持的支付方式'})

    # 订单创建
    # 组织订单信息
    passport_id = request.session.get('passport_id')
    # 订单id: 20171029110830+用户的id
    order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(passport_id)
    # 运费
    transit_price = 10
    # 订单商品总数和总金额
    total_count = 0
    total_price = 0

    # 创建一个保存点
    sid = transaction.savepoint()
    try:
        # 向订单信息表中添加一条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                 passport_id=passport_id,
                                 addr_id=addr_id,
                                 total_count=total_count,
                                 total_price=total_price,
                                 transit_price=transit_price,
                                 pay_method=pay_method)

        # 向订单商品表中添加订单商品的记录
        books_ids = books_ids.split(',')
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % passport_id

        # 遍历获取用户购买的商品信息
        for id in books_ids:
            books = Books.objects.get_books_by_id(books_id=id)
            if books is None:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

            # 获取用户购买的商品数目
            count = conn.hget(cart_key, id)

            # 判断商品的库存
            if int(count) > books.stock:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 5, 'errmsg': '商品库存不足'})

            # 创建一条订单商品记录
            OrderGoods.objects.create(order_id=order_id,
                                      books_id=id,
                                      count=count,
                                      price=books.price)

            # 增加商品的销量，减少商品库存
            books.sales += int(count)
            books.stock -= int(count)
            books.save()

            # 累计计算商品的总数目和总额
            total_count += int(count)
            total_price += int(count) * books.price

        # 更新订单的商品总数目和总金额
        order.total_count = total_count
        order.total_price = total_price
        order.save()
    except Exception as e:
        # 操作数据库出错，进行回滚操作
        transaction.savepoint_rollback(sid)
        return JsonResponse({'res': 7, 'errmsg': '服务器错误'})

    # 清除购物车对应记录
    conn.hdel(cart_key, *books_ids)

    # 事务提交
    transaction.savepoint_commit(sid)
    # 返回应答
    return JsonResponse({'res': 6})
```
然后配置urls.py
```py
    url(r'^commit/$', views.order_commit, name='commit'), # 生成订单
```
然后改写前端页面`place_order.html`，来调用后端提交订单的接口。
```js
{% block bottomfiles %}
    <script type="text/javascript">
        $('#order_btn').click(function() {
            // 获取收货地址的id, 支付方式，用户购买的商品id
            var addr_id = $('input[name="addr_id"]').val()
            var pay_method = $('input[name="pay_style"]:checked').val()
            var books_ids = $(this).attr('books_ids')
            var csrf = $('input[name="csrfmiddlewaretoken"]').val()
            // alert(addr_id+':'+pay_method+':'+books_ids)
            // 发起post请求， 访问/order/commit/
            var params = {
                'addr_id': addr_id,
                'pay_method': pay_method,
                'books_ids': books_ids,
                'csrfmiddlewaretoken': csrf
            }
            $.post('/order/commit/', params, function (data) {
                // 根据json进行处理
                if (data.res == 6){
                    $('.popup_con').fadeIn('fast', function() {
                        setTimeout(function(){
                            $('.popup_con').fadeOut('fast',function(){
                                window.location.href = '/user/order/';
                            });
                        },3000)

                    });
                }
                else {
                    alert(data.errmsg)
                }
            })

        });
    </script>
{% endblock bottomfiles %}
```

那么，我们提交订单的功能也就开发好了。

## 4，接下来我们回过头去把购物车中的提交功能给做了，然后就能做支付功能了。
将cart.html中的去结算功能给出如下的实现。

```html
    <form method="post" action="/order/place/">
    {% for book in books_li %}
    <ul class="cart_list_td clearfix">
        {# 提交表单时，如果checkbox没有被选中，它的值不会被提交 #}
        <li class="col01"><input type="checkbox" name="books_ids" value="{{ book.id }}" checked></li>
        <li class="col02"><img src="{% static book.image %}"></li>
        <li class="col03">{{ book.name }}<br><em>{{ book.price }}元/{{ book.unit }}</em></li>
        <li class="col04">{{ book.unit }}</li>
        <li class="col05">{{ book.price }}</li>
        <li class="col06">
            <div class="num_add">
                <a href="javascript:;" class="add fl">+</a>
                <input type="text" books_id={{ book.id }} class="num_show fl" value="{{ book.count }}">
                <a href="javascript:;" class="minus fl">-</a>   
            </div>
        </li>
        <li class="col07">{{ book.amount }}元</li>
        <li class="col08"><a href="javascript:;">删除</a></li>
    </ul>
    {% endfor %}


    <ul class="settlements">
        {% csrf_token %}
        <li class="col01"><input type="checkbox" name="" checked=""></li>
        <li class="col02">全选</li>
        <li class="col03">合计(不含运费)：<span>¥</span><em>{{ total_price }}</em><br>共计<b>{{ total_count }}</b>件商品</li>
        <li class="col04"><input type="submit" value="去结算"></li>
    </ul>
    </form>
```
好，我们去结算功能也实现了。

## 5，接下来我们将提交订单页面完善一下，完成去支付功能。将支付方式绑定value值，供提交。

```html
<input type="radio" name="pay_style" value="1" checked>
<label class="cash">货到付款</label>
<input type="radio" name="pay_style" value="2">
<label class="weixin">微信支付</label>
<input type="radio" name="pay_style" value="3">
<label class="zhifubao"></label>
<input type="radio" name="pay_style" value="4">
<label class="bank">银行卡支付</label>
```
查缺补漏，发现编辑收货地址功能还没有实现。我们先来编写用户中心地址页的接口。注意，要写在`users/views.py`中。
```python

@login_required
def address(request):
    '''用户中心-地址页'''
    # 获取登录用户的id
    passport_id = request.session.get('passport_id')

    if request.method == 'GET':
        # 显示地址页面
        # 查询用户的默认地址
        addr = Address.objects.get_default_address(passport_id=passport_id)
        return render(request, 'users/user_center_site.html', {'addr': addr, 'page': 'address'})
    else:
        # 添加收货地址
        # 1.接收数据
        recipient_name = request.POST.get('username')
        recipient_addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recipient_phone = request.POST.get('phone')

        # 2.进行校验
        if not all([recipient_name, recipient_addr, zip_code, recipient_phone]):
            return render(request, 'users/user_center_site.html', {'errmsg': '参数不能为空!'})

        # 3.添加收货地址
        Address.objects.add_one_address(passport_id=passport_id,
                                        recipient_name=recipient_name,
                                        recipient_addr=recipient_addr,
                                        zip_code=zip_code,
                                        recipient_phone=recipient_phone)

        # 4.返回应答
        return redirect(reverse('user:address'))
```
然后配置urls.py
```py
    url(r'^address/$', views.address, name='address'), # 用户中心-地址页
```
然后将user_center_site.html拷贝到templates/users文件夹下。并继承base.html。
然后改写模板。
```html
<div class="site_con">
    <dl>
        <dt>当前地址：</dt>
        {% if addr %}
            <dd>{{ addr.recipient_addr }} （{{ addr.recipient_name }} 收） {{ addr.recipient_phone }}</dd>
        {% else %}
            <dd>无</dd>
        {% endif %}
    </dl>
</div>
```
改写form提交表单。
```html
<form method="post" action="/user/address/">
    {% csrf_token %}
    <div class="form_group">
        <label>收件人：</label>
        <input type="text" name="username">
    </div>
    <div class="form_group form_group2">
        <label>详细地址：</label>
        <textarea class="site_area" name="addr"></textarea>
    </div>
    <div class="form_group">
        <label>邮编：</label>
        <input type="text" name="zip_code">
    </div>
    <div class="form_group">
        <label>手机：</label>
        <input type="text" name="phone">
    </div>
    <input type="submit" value="提交" class="info_submit">
</form>
```
好，我们编辑地址的功能已经编写好了。

## 6，完善用户中心
接下来我们进一步完善一下用户中心，把用户中心的订单显示页面给做了。先来实现订单显示的后台接口。
```python
# users/views.py
from django.core.paginator import Paginator

@login_required
def order(request, page):
    '''用户中心-订单页'''
    # 查询用户的订单信息
    passport_id = request.session.get('passport_id')

    # 获取订单信息
    order_li = OrderInfo.objects.filter(passport_id=passport_id)

    # 遍历获取订单的商品信息
    # order->OrderInfo实例对象
    for order in order_li:
        # 根据订单id查询订单商品信息
        order_id = order.order_id
        order_books_li = OrderGoods.objects.filter(order_id=order_id)

        # 计算商品的小计
        # order_books ->OrderGoods实例对象
        for order_books in order_books_li:
            count = order_books.count
            price = order_books.price
            amount = count * price
            # 保存订单中每一个商品的小计
            order_books.amount = amount

        # 给order对象动态增加一个属性order_books_li,保存订单中商品的信息
        order.order_books_li = order_books_li
    
    paginator = Paginator(order_li, 3)      # 每页显示3个订单
    
    num_pages = paginator.num_pages
    
    if not page:        # 首次进入时默认进入第一页
        page = 1
    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)
        
    order_li = paginator.page(page)
    
    if num_pages < 5:
        pages = range(1, num_pages + 1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)

    context = {
        'order_li': order_li,
        'pages': pages,
    }

    return render(request, 'users/user_center_order.html', context)
```
然后配置urls.py。
```
    url(r'^order/(?P<page>\d+)?/?$', views.order, name='order'), # 用户中心-订单页  增加分页功能
```
然后将user_center_order.html拷贝到templates/users文件夹下，并继承base.html。
然后改写模板中的元素，使得后端可以渲染。
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书店-首页{% endblock title %}
{% block topfiles %}
{% endblock topfiles %}
{% block body %}

    <div class="main_con clearfix">
        <div class="left_menu_con clearfix">
            <h3>用户中心</h3>
            <ul>
                <li><a href="{% url 'user:user' %}">· 个人信息</a></li>
                <li><a href="{% url 'user:order' %}" class="active">· 全部订单</a></li>
                <li><a href="{% url 'user:address' %}">· 收货地址</a></li>
            </ul>
        </div>
        <div class="right_content clearfix">
                {% csrf_token %}
                <h3 class="common_title2">全部订单</h3>
                {# OrderInfo #}
                {% for order in order_li %}
                <ul class="order_list_th w978 clearfix">
                    <li class="col01">{{ order.create_time }}</li>
                    <li class="col02">订单号：{{ order.order_id }}</li>
                    <li class="col02 stress">{{ order.status }}</li>
                </ul>

                <table class="order_list_table w980">
                    <tbody>
                        <tr>
                            <td width="55%">
                                {# 遍历出来的order_books是一个OrderGoods对象 #}
                                {% for order_books in order.order_books_li %}
                                <ul class="order_book_list clearfix">                   
                                    <li class="col01"><img src="{% static order_books.books.image %}"></li>
                                    <li class="col02">{{ order_books.books.name }}<em>{{ order_books.books.price }}元/{{ order_books.books.unit }}</em></li>
                                    <li class="col03">{{ order_books.count }}</li>
                                    <li class="col04">{{ order_books.amount }}元</li>
                                </ul>
                                {% endfor %}
                            </td>
                            <td width="15%">{{ order.total_price }}元</td>
                            <td width="15%">{{ order.status }}</td>
                            <td width="15%"><a href="#" pay_method="{{ order.pay_method }}" order_id="{{ order.order_id }}" order_status="{{ order.status }}" class="oper_btn">去付款</a></td>
                        </tr>
                    </tbody>
                </table>
                {% endfor %}

                <div class="pagenation">
                    {% if order_li.has_previous %}
                        <a href="{% url 'user:order' page=order_li.previous_page_number %}">上一页</a>
                    {% endif %}
                    {% for page in pages %}
                        {% if page == order_li.number %}
                            <a href="{% url 'user:order' page=page %}" class="active">{{ page }}</a>
                        {% else %}
                            <a href="{% url 'user:order' page=page %}">{{ page }}</a>
                        {% endif %}
                    {% endfor %}
                    {% if order_li.has_next %}
                        <a href="{% url 'user:order' page=order_li.next_page_number %}">下一页</a>
                    {% endif %}
                </div>
        </div>
    </div>
{% endblock body %}
```
这样我们个人中心的订单的显示页面也就做完了。


## 7，“去付款”功能的实现
接下来我们需要实现“去付款”功能。这里需要集成阿里的支付宝sdk。
我们先来编写后端代码。

生成秘钥文件
```
openssl
OpenSSL> genrsa -out app_private_key.pem 2048  # 私钥
OpenSSL> rsa -in app_private_key.pem -pubout -out app_public_key.pem # 导出公钥
OpenSSL> exit
```
设置支付宝沙箱公钥
支付宝逐渐转换为RSA2秘钥，可以使用官方工具生成秘钥
```
支付宝沙箱地址：https://openhome.alipay.com/platform/appDaily.htm?tab=info
生成RSA2教程：https://docs.open.alipay.com/291/106130
测试用秘钥： 链接: https://pan.baidu.com/s/1HpAoD8heei18rXdjRIZdUg 密码: rcip
```
设置本地公钥&私钥格式
```
app_private_key_string.pem

-----BEGIN RSA PRIVATE KEY-----
         私钥内容
-----END RSA PRIVATE KEY-----


alipay_public_key_string.pem

-----BEGIN PUBLIC KEY-----
         公钥内容
-----END PUBLIC KEY-----
```


```python
# order/views.py
# 前端需要发过来的参数:order_id
# post
# 接口文档：https://github.com/fzlee/alipay/blob/master/README.zh-hans.md
# 安装python-alipay-sdk
# pip install python-alipay-sdk --upgrade

from alipay import AliPay

@login_required
def order_pay(request):
    '''订单支付'''

    # 接收订单id
    order_id = request.POST.get('order_id')

    # 数据校验
    if not order_id:
        return JsonResponse({'res': 1, 'errmsg': '订单不存在'})

    try:
        order = OrderInfo.objects.get(order_id=order_id,
                                      status=1,
                                      pay_method=3)
    except OrderInfo.DoesNotExist:
        return JsonResponse({'res': 2, 'errmsg': '订单信息出错'})


    # 将app_private_key.pem和app_public_key.pem拷贝到order文件夹下。
    app_private_key_path = os.path.join(settings.BASE_DIR, 'order/app_private_key.pem')
    alipay_public_key_path = os.path.join(settings.BASE_DIR, 'order/app_public_key.pem')

    app_private_key_string = open(app_private_key_path).read()
    alipay_public_key_string = open(alipay_public_key_path).read()

    # 和支付宝进行交互
    alipay = AliPay(
        appid="2016091500515408", # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type = "RSA2",  # RSA 或者 RSA2
        debug = True,  # 默认False
    )

    # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    total_pay = order.total_price + order.transit_price # decimal
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_id, # 订单id
        total_amount=str(total_pay), # Json传递，需要将浮点转换为字符串
        subject='尚硅谷书城%s' % order_id,
        return_url=None,
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    # 返回应答
    pay_url = settings.ALIPAY_URL + '?' + order_string
    return JsonResponse({'res': 3, 'pay_url': pay_url, 'message': 'OK'})
```
然后我们把公钥和私钥拷贝到order文件夹下。
然后我们需要获取用户的支付结果。
```py
# 前端需要发过来的参数:order_id
# post
from alipay import AliPay

@login_required
def check_pay(request):
    '''获取用户支付的结果'''

    passport_id = request.session.get('passport_id')
    # 接收订单id
    order_id = request.POST.get('order_id')

    # 数据校验
    if not order_id:
        return JsonResponse({'res': 1, 'errmsg': '订单不存在'})

    try:
        order = OrderInfo.objects.get(order_id=order_id,
                                      passport_id=passport_id,
                                      pay_method=3)
    except OrderInfo.DoesNotExist:
        return JsonResponse({'res': 2, 'errmsg': '订单信息出错'})

    app_private_key_path = os.path.join(settings.BASE_DIR, 'order/app_private_key.pem')
    alipay_public_key_path = os.path.join(settings.BASE_DIR, 'order/app_public_key.pem')

    app_private_key_string = open(app_private_key_path).read()
    alipay_public_key_string = open(alipay_public_key_path).read()

    # 和支付宝进行交互
    alipay = AliPay(
        appid="2016091500515408", # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type = "RSA2",  # RSA 或者 RSA2
        debug = True,  # 默认False
    )

    while True:
        # 进行支付结果查询
        result = alipay.api_alipay_trade_query(order_id)
        code = result.get('code')
        if code == '10000' and result.get('trade_status') == 'TRADE_SUCCESS':
            # 用户支付成功
            # 改变订单支付状态
            order.status = 2 # 待发货
            # 填写支付宝交易号
            order.trade_id = result.get('trade_no')
            order.save()
            # 返回数据
            return JsonResponse({'res':3, 'message':'支付成功'})
        elif code == '40004' or (code == '10000' and result.get('trade_status') == 'WAIT_BUYER_PAY'):
            # 支付订单还未生成，继续查询
            # 用户还未完成支付，继续查询
            time.sleep(5)
            continue
        else:
            # 支付出错
            return JsonResponse({'res':4, 'errmsg':'支付出错'})
```
配置支付宝gateway到配置文件中。
```py
ALIPAY_URL='https://openapi.alipaydev.com/gateway.do'
```
配置urls.py。
```py
    url(r'^pay/$', views.order_pay, name='pay'), # 订单支付
    url(r'^check_pay/$', views.check_pay, name='check_pay'), # 查询支付结果
```
然后编写前端jquery代码，来处理支付后的结果，比如支付成功以后刷新页面。以下代码写入`templates/users/user_center_order.html`中。
```js
{% block bottomfiles%}
    <script>
    $(function () {
        $('.oper_btn').click(function () {
            // 获取订单id和订单的状态
            order_id = $(this).attr('order_id')
            order_status = $(this).attr('order_status')
            csrf = $('input[name="csrfmiddlewaretoken"]').val()
            params = {'order_id':order_id, 'csrfmiddlewaretoken':csrf}
            if (order_status == 1){
                $.post('/order/pay/', params, function (data) {
                    if (data.res == 3){
                        // 把用户引导支付页面
                        window.open(data.pay_url)
                        // 查询用户的支付结果
                        $.post('/order/check_pay/', params, function (data) {
                            if (data.res == 3){
                                alert('支付成功')
                                // 重新刷新页面
                                location.reload()
                            }
                            else{
                                alert(data.errmsg)
                            }
                        })
                    }
                    else{
                        alert(data.errmsg)
                    }
                })
            }
        })
    })
    </script>
{% endblock bottomfiles %}
```
好，我们支付功能也编写好了。

# <a id="7">7，使用缓存</a>
使用redis缓存首页的页面。
```py
from django.views.decorators.cache import cache_page
@cache_page(60 * 15)
def index(request):
    '''显示首页'''
    ...
```
别忘了把redis启动起来。
在settings.py中配置redis缓存。
```py
# pip install django-redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": ""
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```


# <a id="8">8，评论功能的实现</a>
先来新建comments应用。
```
$ python manage.py startapp comments
```
然后设计数据库表结构。

```python
from django.db import models
from db.base_model import BaseModel
from users.models import Passport
from books.models import Books
# Create your models here.
class Comments(BaseModel):
    disabled = models.BooleanField(default=False, verbose_name="禁用评论")
    user = models.ForeignKey('users.Passport', verbose_name="用户ID")
    book = models.ForeignKey('books.Books', verbose_name="书籍ID")
    content = models.CharField(max_length=1000, verbose_name="评论内容")

    class Meta:
        db_table = 's_comment_table'
```

这里要注意外键的使用和理解。
然后我们要在配置文件里注册app。

```python
# bookstore/settings.py
INSTALLED_APPS = (
    ...
    'comments', # 评论模块
    ...
)
```
然后我们来写评论应用的视图函数。视图函数使用redis作为缓存，缓存了get请求的结果。
```python
# comments/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from comments.models import Comments
from books.models import Books
from users.models import Passport
from django.views.decorators.csrf import csrf_exempt
import json
import redis
from utils.decorators import login_required
# Create your views here.
# 设置过期时间
EXPIRE_TIME = 60 * 10
# 连接redis数据库
pool = redis.ConnectionPool(host='localhost', port=6379, db=2)
redis_db = redis.Redis(connection_pool=pool)

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@login_required
def comment(request, books_id):
    book_id = books_id
    if request.method == 'GET':
        # 先在redis里面寻找评论
        c = redis_db.get('comment_%s' % book_id)
        try:
            c = c.decode('utf-8')
        except:
            pass
        print('c: ', c)
        if c:
            return JsonResponse({
                    'code': 200,
                    'data': json.loads(c),
                })
        else:
            # 找不到，就从数据库里面取
            comments = Comments.objects.filter(book_id=book_id)
            data = []
            for c in comments:
                data.append({
                    'user_id': c.user_id,
                    'content': c.content,
                })

            res = {
                'code': 200,
                'data': data, 
            }
            try:
                redis_db.setex('comment_%s' % book_id, json.dumps(data), EXPIRE_TIME)
            except Exception as e:
                print('e: ', e)
            return JsonResponse(res)

    else:
        params = json.loads(request.body.decode('utf-8'))

        book_id = params.get('book_id')
        user_id = params.get('user_id')
        content = params.get('content')

        book = Books.objects.get(id=book_id)
        user = Passport.objects.get(id=user_id)

        comment = Comments(book=book, user=user, content=content)
        comment.save()

        return JsonResponse({
                'code': 200,
                'msg': '评论成功',
            })

```
然后注册url。
```python
# 根urls.py: bookstore: urls.py
urlpatterns = [
    ...
    url(r'^comment/', include('comments.urls', namespace='comment')), # 评论模块
    ...
]
```
comments app的url注册。
```python
from django.conf.urls import url
from comments import views

urlpatterns = [
    url(r'comment/(?P<books_id>\d+)/$', views.comment, name='comment'), # 评论内容
]
```
注册好url以后，我们要编写detail.html里面的前端代码了。
```html
            <div class="operate_btn">
                {% csrf_token %}
                <a href="javascript:;" class="buy_btn">立即购买</a>
                <a href="javascript:;" books_id="{{ books.id }}" class="add_cart" id="add_cart">加入购物车</a>
                <a href="#" id="write-comment" class="comment">我要写评论</a>
            </div>
            <div style="display:flex;" id="comment-input" data-bookid="{{ books.id }}" data-userid="{{ request.session.passport_id }}">
                <div>
                    <input type="text" placeholder="评论内容">
                </div>
                <div id="submit-comment">
                    <button>
                      提交评论
                    </button>
                </div>
            </div>
```

再增加id-book_detail 和id-book_comment 增加点击效果 
```html
    <div class="r_wrap fr clearfix">
        <ul class="detail_tab clearfix">
            <li class="active" id="detail">商品介绍</li>
            <li id="comment">评论</li>
        </ul>

        <div class="tab_content" >
            <dl id="book_detail">
                <dt>商品详情：</dt>
                <dd>{{ books.detail | safe }}</dd>
            </dl>
            <dl id="book_comment" style="display: none; font-size: 15px; color: #0a0a0a">
                <dt>用户评论:</dt>
                <dd></dd>
            </dl>
        </div>
    </div>
```


然后写样式。
```css
<style type="text/css">
.comment {
    background-color: #c40000;
    color: #fff;
    margin-left: 10px;
    position: relative;
    z-index: 10;
    display: inline-block;
    width: 178px;
    height: 38px;
    border: 1px solid #c40000;
    font-size: 14px;
    line-height: 38px;
    text-align: center;
}
</style>
```
以及提交评论的js代码。
```javascript
    // 获取评论
    $.ajax({
        url: '/comment/comment/' + $('#comment-input').data('bookid'),
        success: function (res) {
            if (res.code === 200) {
                var data = res.data;
                console.log(data);
                var div_head = '<div>';
                var div_tail = '</div>';
                var dom_element = ''
                for(i = 0; i < data.length; i++) {
                    var head = '<div>';
                    var tail = '</div>';
                    var temp = head + '<span>' + data[i].user_id + '</span>' + '<br>' + '<span>' + data[i].content + '</span>' + tail;
                    dom_element += temp;
                }
                dom_element = div_head + dom_element + div_tail;
                $('#book_comment').append(dom_element);
            }
        }
    })

    $('#detail').click(function () {
        $(this).addClass('active');
        $('#comment').removeClass('active');
        $('#book_comment').hide();
        $('#book_detail').show();
    })
    $('#comment').click(function () {
        $(this).addClass('active');
        $('#detail').removeClass('active');
        $('#book_comment').show();
        $('#book_detail').hide();
    })
    $('#write-comment').click(function () {
        $('#comment-input').show();
    })
    $('#submit-comment').click(function () {
        var book_id = $('#comment-input').data('bookid');
        var user_id = $('#comment-input').data('userid');
        var content = $('#comment-input input').val();
        var data = {
            book_id: book_id,
            user_id: user_id,
            content: content,
        }
        console.log('content: ', content);
        $.ajax({
            type: 'POST',
            url: '/comment/comment/' + book_id + '/',
            data: JSON.stringify(data),
            success: function (res) {
                if (res.code === 200) {
                    // console.log('res: ', res)
                    $('#comment-input').hide();
                }
            }
        })
    })
```
这样评论功能就做好了。

# <a id="9">9，发送邮件功能实现。</a>

## 1，同步发送邮件

先在配置文件中配置邮件相关参数。

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.126.com'
# 126和163邮箱的SMTP端口为25； QQ邮箱使用的SMTP端口为465
EMAIL_PORT = 25
# 如果使用QQ邮箱发送邮件，需要开启SSL加密, 如果在aliyun上部署，也需要开启ssl加密，同时修改端口为EMAIL_PORT = 465
# EMAIL_USE_SSL = True
# 发送邮件的邮箱
EMAIL_HOST_USER = 'xxxxxxxx@126.com'
# 在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'xxxxxxxx'
# 收件人看到的发件人
EMAIL_FROM = 'shangguigu<xxxxxxxx@126.com>'
```
在注册页的视图函数里写发邮件的代码。
```python
# users/views.py
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
```
itsdangerous是一个产生token的库，有flask的作者编写。
```python
def register_handle(request):
    '''进行用户注册处理'''
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')

    # 进行数据校验
    if not all([username, password, email]):
        # 有数据为空
        return render(request, 'users/register.html', {'errmsg':'参数不能为空!'})

    # 判断邮箱是否合法
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        # 邮箱不合法
        return render(request, 'users/register.html', {'errmsg':'邮箱不合法!'})

    p = Passport.objects.check_passport(username=username)

    if p:
        return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})

    # 进行业务处理:注册，向账户系统中添加账户
    # Passport.objects.create(username=username, password=password, email=email)
    passport = Passport.objects.add_one_passport(username=username, password=password, email=email)

    # 生成激活的token itsdangerous
    serializer = Serializer(settings.SECRET_KEY, 3600)
    token = serializer.dumps({'confirm':passport.id}) # 返回bytes
    token = token.decode()

    # 给用户的邮箱发激活邮件
    send_mail('尚硅谷书城用户激活', '', settings.EMAIL_FROM, [email], html_message='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>' % token)

    # 注册完，还是返回注册页。
    return redirect(reverse('books:index'))
```

register_handle函数变为以上代码，增加了发送邮件的功能。注意这里我们没有实现check_passport函数。所以要在`users/models.py`中的`PassportManager`中实现这个函数。

```python
class PassportManager(models.Manager):
    ...
    def check_passport(self, username):
        try:
            passport = self.get(username=username)
        except self.model.DoesNotExist:
            passport = None
        if passport:
            return True
        return False
```

## 2，使用消息队列celery来异步发送邮件。
首先配置celery。在bookstore文件夹下面。
```python
# bookstore/celery.py
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings')

app = Celery('bookstore', broker='redis://127.0.0.1:6379/6')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
```
然后在users app中编写异步任务。
```python
# users/tasks.py
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

@shared_task
def send_active_email(token, username, email):
    '''发送激活邮件'''
    subject = '尚硅谷书城用户激活' # 标题
    message = ''
    sender = settings.EMAIL_FROM # 发件人
    receiver = [email] # 收件人列表
    html_message = '<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>'%token
    send_mail(subject, message, sender, receiver, html_message=html_message)
```
然后在视图函数中导入异步任务。
```python
from users.tasks import send_active_email
def register_handle(request):
    ...
    send_active_email.delay(token, username, email)
    ...
```
然后改写根应用文件夹里的__init__.py，将整个文件改为：
```python

import pymysql
pymysql.install_as_MySQLdb()
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ['celery_app']
```
然后运行:(在根目录，和manage.py同级)
```
$ celery -A bookstore worker -l info
```

# <a id="10">10，登陆验证码功能实现</a>

将项目中的`Ubuntu-RI.ttf`字体文件拷贝到你的项目的根目录下面。

```python
# users/views.py
from django.http import HttpResponse
from django.conf import settings
import os
def verifycode(request):
    #引入绘图模块
    from PIL import Image, ImageDraw, ImageFont
    #引入随机函数模块
    import random
    #定义变量，用于画面的背景色、宽、高
    bgcolor = (random.randrange(20, 100), random.randrange(
        20, 100), 255)
    width = 100
    height = 25
    #创建画面对象
    im = Image.new('RGB', (width, height), bgcolor)
    #创建画笔对象
    draw = ImageDraw.Draw(im)
    #调用画笔的point()函数绘制噪点
    for i in range(0, 100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill=fill)
    #定义验证码的备选值
    str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    #随机选取4个值作为验证码
    rand_str = ''
    for i in range(0, 4):
        rand_str += str1[random.randrange(0, len(str1))]
    #构造字体对象
    font = ImageFont.truetype(os.path.join(settings.BASE_DIR, "Ubuntu-RI.ttf"), 15)
    #构造字体颜色
    fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
    #绘制4个字
    draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
    draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
    draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
    draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
    #释放画笔
    del draw
    #存入session，用于做进一步验证
    request.session['verifycode'] = rand_str
    #内存文件操作
    import io
    buf = io.BytesIO()
    #将图片保存在内存中，文件类型为png
    im.save(buf, 'png')
    #将内存中的图片数据返回给客户端，MIME类型为图片png
    return HttpResponse(buf.getvalue(), 'image/png')
```
然后在urls.py中配置url。
```
    url(r'^verifycode/$', views.verifycode, name='verifycode'), # 验证码功能
```
编写前端代码。在前段代码中的Form里添加以下代码。
```html
// templates/users/login.html
<div style="top: 100px; position: absolute;">
    <input type="text" id="vc" name="vc">
    <img id='verifycode' src="/user/verifycode/" onclick="this.src='/user/verifycode/?'+Math.random()" alt="CheckCode"/>
</div>
```
前端需要向后端post数据。post以下数据
```javascript
var username = $('#username').val()
var password = $('#pwd').val()
var csrf = $('input[name="csrfmiddlewaretoken"]').val()
var remember = $('input[name="remember"]').prop('checked')
var vc = $('input[name="vc"]').val()
// 发起ajax请求
var params = {
    'username': username,
    'password': password,
    'csrfmiddlewaretoken': csrf,
    'remember': remember,
    'verifycode': vc,
}
```
然后在后端进行校验。login_check函数改为以下代码实现。
```python
def login_check(request):
    '''进行用户登录校验'''
    # 1.获取数据
    username = request.POST.get('username')
    password = request.POST.get('password')
    remember = request.POST.get('remember')
    verifycode = request.POST.get('verifycode')

    # 2.数据校验
    if not all([username, password, remember, verifycode]):
        # 有数据为空
        return JsonResponse({'res': 2})

    if verifycode.upper() != request.session['verifycode']:
        return JsonResponse({'res': 2})

    # 3.进行处理:根据用户名和密码查找账户信息
    passport = Passport.objects.get_one_passport(username=username, password=password)

    if passport:
        # 用户名密码正确
        # 获取session中的url_path
        # if request.session.has_key('url_path'):
        #     next_url = request.session.get('url_path')
        # else:
        #     next_url = reverse('books:index')
        next_url = reverse('books:index') # /user/
        jres = JsonResponse({'res': 1, 'next_url': next_url})

        # 判断是否需要记住用户名
        if remember == 'true':
            # 记住用户名
            jres.set_cookie('username', username, max_age=7*24*3600)
        else:
            # 不要记住用户名
            jres.delete_cookie('username')

        # 记住用户的登录状态
        request.session['islogin'] = True
        request.session['username'] = username
        request.session['passport_id'] = passport.id
        return jres
    else:
        # 用户名或密码错误
        return JsonResponse({'res': 0})
```
那我们的验证码功能就实现了。

# <a id="11">11，全文检索的实现</a>
添加全文检索应用，在配置文件中。
```py
INSTALLED_APPS = (
    ...
    'haystack',
)
```
在配置文件中写入以下配置。
```py
# 全文检索配置
HAYSTACK_CONNECTIONS = {
    'default': {
        # 使用whoosh引擎
        # 'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine',
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        # 索引文件路径
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}

# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

HAYSTACK_SEARCH_RESULTS_PER_PAGE = 6 # 指定搜索结果每页的条数
```
在urls.py中配置。
```
urlpatterns = [
    ...
    url(r'^search/', include('haystack.urls')),
]
```
在books应用目录下建立search_indexes.py文件。
```py
from haystack import indexes
from books.models import Books


# 指定对于某个类的某些数据建立索引, 一般类名:模型类名+Index
class BooksIndex(indexes.SearchIndex, indexes.Indexable):
    # 指定根据表中的哪些字段建立索引:比如:商品名字 商品描述
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Books

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

```
在目录“templates/search/indexes/books/”下创建“books_text.txt”文件
```
{{ object.name }} # 根据书籍的名称建立索引
{{ object.desc }} # 根据书籍的描述建立索引
{{ object.detail }} # 根据书籍的详情建立索引
```
在目录“templates/search/”下建立search.html。
```html
{% extends 'base.html' %}
{% load staticfiles %}
{% block title %}尚硅谷书城-书籍搜索结果列表{% endblock title %}
{% block body %}
    <div class="breadcrumb">
        <a href="#">{{ query }}</a>
        <span>></span>
        <a href="#">搜索结果如下:</a>
    </div>

    <div class="main_wrap clearfix">
            <ul class="book_type_list clearfix">
                {% for item in page %}
                    <li>
                        <a href="{% url 'books:detail' books_id=item.object.id %}"><img src="{% static item.object.image %}"></a>
                        <h4><a href="{% url 'books:detail' books_id=item.object.id %}">{{ item.object.name }}</a></h4>
                        <div class="operate">
                            <span class="price">￥{{ item.object.price }}</span>
                            <span class="unit">{{ item.object.unit }}</span>
                            <a href="#" class="add_books" title="加入购物车"></a>
                        </div>
                    </li>
                {% endfor %}
            </ul>
            <div class="pagenation">
                {% if page.has_previous %}
                    <a href="/search/?q={{ query }}&page={{ page.previous_page_number }}"><上一页</a>
                {% endif %}
                {% for pindex in paginator.page_range %}
                    {% if pindex == page.number %}
                        <a href="/search/?q={{ query }}&page={{ pindex }}" class="active">{{ pindex }}</a>
                    {% else %}
                        <a href="/search/?q={{ query }}&page={{ pindex }}">{{ pindex }}</a>
                    {% endif %}
                {% endfor %}
                {% if page.has_next %}
                    <a href="/search/?q={{ query }}&page={{ page.next_page_number }}">下一页></a>
                {% endif %}
            </div>
    </div>
{% endblock body %}
```
建立ChineseAnalyzer.py文件。
保存在haystack的安装文件夹下，路径如“/home/python/.virtualenvs/django_py2/lib/python3.5/site-packages/haystack/backends”
```py
import jieba
from whoosh.analysis import Tokenizer, Token


class ChineseTokenizer(Tokenizer):
    def __call__(self, value, positions=False, chars=False,
                 keeporiginal=False, removestops=True,
                 start_pos=0, start_char=0, mode='', **kwargs):
        t = Token(positions, chars, removestops=removestops, mode=mode,
                  **kwargs)
        seglist = jieba.cut(value, cut_all=True)
        for w in seglist:
            t.original = t.text = w
            t.boost = 1.0
            if positions:
                t.pos = start_pos + value.find(w)
            if chars:
                t.startchar = start_char + value.find(w)
                t.endchar = start_char + value.find(w) + len(w)
            yield t


def ChineseAnalyzer():
    return ChineseTokenizer()
```
复制whoosh_backend.py文件，改名为whoosh_cn_backend.py
注意：复制出来的文件名，末尾会有一个空格，记得要删除这个空格
然后将下面这一行代码写入`whoosh_cn_backend.py`文件中。
```py
from .ChineseAnalyzer import ChineseAnalyzer
```
然后查找下面的这一行代码
```py
analyzer=StemmingAnalyzer()
```
改为
```py
analyzer=ChineseAnalyzer()
```
生成索引
```py
$ python manage.py rebuild_index
```
在模板`base.html`中创建搜索栏
```
<form method='get' action="/search/" target="_blank">
    <input type="text" name="q">
    <input type="submit" value="查询">
</form>
```

# <a id="12">12，用户激活功能的实现</a>
首先编写视图函数：
```py
def register_active(request, token):
    '''用户账户激活'''
    serializer = Serializer(settings.SECRET_KEY, 3600)
    try:
        info = serializer.loads(token)
        passport_id = info['confirm']
        # 进行用户激活
        passport = Passport.objects.get(id=passport_id)
        passport.is_active = True
        passport.save()
        # 跳转的登录页
        return redirect(reverse('user:login'))
    except SignatureExpired:
        # 链接过期
        return HttpResponse('激活链接已过期')
```
然后配置url就完成了。
```
    url(r'^active/(?P<token>.*)/$', views.register_active, name='active'), # 用户激活
```

# <a id="13">13，用户中心最近浏览功能的实现</a>
最近浏览使用redis实现。重新编写books/views.py中的detail函数，每次点击商品，都将商品信息写入redis，作为最近浏览的数据。
```py
# books/views.py
def detail(request, books_id):
    '''显示商品的详情页面'''
    # 获取商品的详情信息
    books = Books.objects.get_books_by_id(books_id=books_id)

    if books is None:
        # 商品不存在，跳转到首页
        return redirect(reverse('books:index'))

    # 新品推荐
    books_li = Books.objects.get_books_by_type(type_id=books.type_id, limit=2, sort='new')

    # 用户登录之后，才记录浏览记录
    # 每个用户浏览记录对应redis中的一条信息 格式:'history_用户id':[10,9,2,3,4]
    # [9, 10, 2, 3, 4]
    if request.session.has_key('islogin'):
        # 用户已登录，记录浏览记录
        con = get_redis_connection('default')
        key = 'history_%d' % request.session.get('passport_id')
        # 先从redis列表中移除books.id
        con.lrem(key, 0, books.id)
        con.lpush(key, books.id)
        # 保存用户最近浏览的5个商品
        con.ltrim(key, 0, 4)

    # 定义上下文
    context = {'books': books, 'books_li': books_li}

    # 使用模板
    return render(request, 'books/detail.html', context)
```
然后重写用户中心的视图函数代码：users/views.py中的user函数。
```py
@login_required
def user(request):
    '''用户中心-信息页'''
    passport_id = request.session.get('passport_id')
    # 获取用户的基本信息
    addr = Address.objects.get_default_address(passport_id=passport_id)

    # 获取用户的最近浏览信息
    con = get_redis_connection('default')
    key = 'history_%d' % passport_id
    # 取出用户最近浏览的5个商品的id
    history_li = con.lrange(key, 0, 4)
    # history_li = [21,20,11]
    # print(history_li)
    # 查询数据库,获取用户最近浏览的商品信息
    # books_li = Books.objects.filter(id__in=history_li)
    books_li = []
    for id in history_li:
        books = Books.objects.get_books_by_id(books_id=id)
        books_li.append(books)

    return render(request, 'users/user_center_info.html', {'addr': addr,
                                                           'page': 'user',
                                                           'books_li': books_li})
```
然后编写前端页面。重写user_center_info.html中最近浏览下面的html内容。
```html
<h3 class="common_title2">最近浏览</h3>
<div class="has_view_list">
    <ul class="book_type_list clearfix">
        {% for books in books_li %}
            <li>
                <a href="{% url 'books:detail' books_id=books.id %}"><img src="{% static books.image %}"></a>
                <h4><a href="{% url 'books:detail' books_id=books.id %}">{{ books.name }}</a></h4>
                <div class="operate">
                    <span class="price">￥{{ books.price }}</span>
                    <span class="unit">{{ books.unit }}</span>
                    <a href="#" class="add_books" title="加入购物车"></a>
                </div>
            </li>
        {% endfor %}
    </ul>
</div>
```
最近浏览功能就实现了。

# <a id="14">14，前端过滤器实现</a>
在users文件夹中新建templatetags文件夹。然后新建__init__.py文件，这是空文件。然后新建filters.py文件。
```python
from django.template import Library

# 创建一个Library类的对象
register = Library()


# 创建一个过滤器函数
@register.filter
def order_status(status):
    '''返回订单状态对应的字符串'''
    status_dict =  {
        1:"待支付",
        2:"待发货",
        3:"待收货",
        4:"待评价",
        5:"已完成",
    }
    return status_dict[status]
```
然后在根应用settings.py里面添加应用：
```python
INSTALLED_APPS = (
    ...
    'users.templatetags.filters', # 过滤器功能
)
```
这样我们就能在前端使用这个过滤器了。
```html
<td width="15%">{{ order.status | order_status }}</td>
```
注意要在页面里
```html
{% load filters %}
```

# <a id="15">15，使用gunicorn+nginx+django进行部署</a>
安装nginx。
```
sudo apt install nginx
```
先看nginx配置文件nginx.conf, 一般情况下, 路径为`/etc/nginx/nginx.conf`
```
user root;
worker_processes auto;
pid /run/nginx.pid;

events {
        worker_connections 768;
        # multi_accept on;
}

http {

        ##
        # Basic Settings
        ##

        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        types_hash_max_size 2048;
        # server_tokens off;

        # server_names_hash_bucket_size 64;
        # server_name_in_redirect off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        ##
        # SSL Settings
        ##

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
        ssl_prefer_server_ciphers on;

        ##
        # Logging Settings
        ##

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        ##
        # Gzip Settings
        ##

        gzip on;
        gzip_disable "msie6";
        # gzip_vary on;
        # gzip_proxied any;
        # gzip_comp_level 6;
        # gzip_buffers 16 8k;
        # gzip_http_version 1.1;
        # gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        ##
        # Virtual Host Configs
        ##

        include /etc/nginx/conf.d/*.conf;
        #include /etc/nginx/sites-enabled/*;

        server {
            listen 80;
            server_name localhost;
            location / {
                proxy_pass http://0.0.0.0:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            }
            error_page 500 502 503 504 /50x.html;

            location = /50x.html {
                root html;
            }
            location /media {
                alias /root/bookstore/bookstore/static;
            }
            location /static {
                alias /root/bookstore/bookstore/collect_static;
            }
        }
}
```
如果`nginx`没启动，则执行
```s
$ nginx
```
如果`nginx`已经启动，则执行以下命令重启
```s
$ nginx -s reload
```
然后在根目录bookstore新建文件夹collect_static。
注意要在配置文件`settings.py`中写一行
```py
STATIC_ROOT = os.path.join(BASE_DIR, 'collect_static')
```
然后在根目录运行`python manage.py collectstatic`命令，这个命令用来收集静态文件。
并将books/models.py中添加代码：
```py
from django.core.files.storage import FileSystemStorage
fs = FileSystemStorage(location='/root/bookstore/bookstore/collect_static')
class Books(BaseModel):
    ...
    image = models.ImageField(storage=fs, upload_to='books', verbose_name='商品图片')
    ...
```
然后在根目录运行`gunicorn`。安装`gunicorn`，`pip install gunicorn`
```
nohup gunicorn -w 3 -b 0.0.0.0:8000 bookstore.wsgi:application &
```

# <a id="16">16，django日志模块的使用</a>

首先将下面的代码添加到配置文件`settings.py`。

```py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {             # 日志输出的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {               # 处理日志的函数
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/log/debug.log',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
        },
        'django.request': {     # 日志的命名空间
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

然后在根目录新建文件夹`log`。
```
mkdir log
```

然后在代码中添加日志相关的代码。例如，在`books/views.py`中，添加以下代码：

```py
import logging
logger = logging.getLogger('django.request')
```
在`books/views.py`中的`index`函数中添加一行：
```py
logger.info(request.body)
```

就会发现当我们访问首页的时候，在`log/debug.log`中有日志信息。


# <a id="17">17，中间件的编写</a>

在`utils`文件夹中新建`middleware.py`文件。

```py
from django import http
# 中间件示例，打印中间件执行语句
class BookMiddleware(object):
    def process_request(self, request):
        print("Middleware executed")

# 分别处理收到的请求和发出去的相应，要理解中间件的原理。
class AnotherMiddleware(object):
    def process_request(self, request):
        print("Another middleware executed")

    def process_response(self, request, response):
        print("AnotherMiddleware process_response executed")
        return response

# 记录用户访问的url地址
class UrlPathRecordMiddleware(object):
    '''记录用户访问的url地址'''
    EXCLUDE_URLS = ['/user/login/', '/user/logout/', '/user/register/']
    # 1./user/ 记录 url_path = /user/
    # 2./user/login/ url_path = /user/
    # 3./user/login_check/  url_path = /user/
    def process_view(self, request, view_func, *view_args, **view_kwargs):
        # 当用户请求的地址不在排除的列表中，同时不是ajax的get请求
        if request.path not in UrlPathRecordMiddleware.EXCLUDE_URLS and not request.is_ajax() and request.method == 'GET':
            request.session['url_path'] = request.path

BLOCKED_IPS = []
# 拦截在BLOCKED_IPS中的IP
class BlockedIpMiddleware(object):
    def process_request(self, request):
        if request.META['REMOTE_ADDR'] in BLOCKED_IPS:
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
```

然后在配置文件`settings.py`中，写入中间件类的名字。

```py
MIDDLEWARE_CLASSES = (
    ...
    'utils.middleware.BookMiddleware',
    'utils.middleware.AnotherMiddleware',
    'utils.middleware.UrlPathRecordMiddleware',
    'utils.middleware.BlockedIpMiddleware',
)
```

这样就可以使用中间件了。
