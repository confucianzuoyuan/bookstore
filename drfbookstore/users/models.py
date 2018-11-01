from django.db import models
from db.base_model import BaseModel

# Create your models here.
class Passport(BaseModel):
    '''用户模型类'''
    username = models.CharField(max_length=20, verbose_name='用户名称')
    password = models.CharField(max_length=40, verbose_name='用户密码')
    email = models.EmailField(verbose_name='用户邮箱')
    is_active = models.BooleanField(default=False, verbose_name='激活状态')

    class Meta:
        db_table = 's_user_account'

class Address(BaseModel):
    '''地址模型类'''
    recipient_name = models.CharField(max_length=20, verbose_name='收件人')
    recipient_addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮政编码')
    recipient_phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    passport = models.ForeignKey('Passport', verbose_name='账户', on_delete=models.CASCADE)

    class Meta:
        db_table = 's_user_address'
