# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Reporting', '0007_add_flag_fields_interaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='interaction',
            name='ready',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
