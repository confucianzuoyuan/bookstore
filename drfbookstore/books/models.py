from django.db import models
from db.base_model import BaseModel
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
    detail = models.TextField(verbose_name='商品详情')
    image = models.ImageField(upload_to='books', verbose_name='商品图片')
    status = models.SmallIntegerField(default=ONLINE, choices=status_choices, verbose_name='商品状态')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 's_books'
        verbose_name = '书籍'
        verbose_name_plural = verbose_name

