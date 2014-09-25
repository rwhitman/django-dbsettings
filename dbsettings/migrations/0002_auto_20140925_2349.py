# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbsettings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='value',
            field=models.TextField(blank=True),
        ),
    ]
