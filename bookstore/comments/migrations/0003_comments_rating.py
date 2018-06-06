# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0002_comments_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='comments',
            name='rating',
            field=models.IntegerField(verbose_name='评分', default=1),
        ),
    ]
