# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_address'),
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('is_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('count', models.IntegerField(verbose_name='商品数量', default=1)),
                ('price', models.DecimalField(decimal_places=2, verbose_name='商品价格', max_digits=10)),
                ('books', models.ForeignKey(verbose_name='订单商品', to='books.Books')),
            ],
            options={
                'db_table': 's_order_books',
            },
        ),
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('is_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('order_id', models.CharField(serialize=False, verbose_name='订单编号', primary_key=True, max_length=64)),
                ('total_count', models.IntegerField(verbose_name='商品总数', default=1)),
                ('total_price', models.DecimalField(decimal_places=2, verbose_name='商品总价', max_digits=10)),
                ('transit_price', models.DecimalField(decimal_places=2, verbose_name='订单运费', max_digits=10)),
                ('pay_method', models.SmallIntegerField(verbose_name='支付方式', choices=[(1, '货到付款'), (2, '微信支付'), (3, '支付宝'), (4, '银联支付')], default=1)),
                ('status', models.SmallIntegerField(verbose_name='订单状态', choices=[(1, '待支付'), (2, '待发货'), (3, '待收货'), (4, '待评价'), (5, '已完成')], default=1)),
                ('trade_id', models.CharField(verbose_name='支付编号', unique=True, null=True, max_length=100, blank=True)),
                ('addr', models.ForeignKey(verbose_name='收货地址', to='users.Address')),
                ('passport', models.ForeignKey(verbose_name='下单账户', to='users.Passport')),
            ],
            options={
                'db_table': 's_order_info',
            },
        ),
        migrations.AddField(
            model_name='ordergoods',
            name='order',
            field=models.ForeignKey(verbose_name='所属订单', to='order.OrderInfo'),
        ),
    ]
