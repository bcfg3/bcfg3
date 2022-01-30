# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Reporting', '0008_add_ready_flag_interaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, db_index=True)),
                ('hash_key', models.BigIntegerField(editable=False, db_index=True)),
                ('state', models.IntegerField(choices=[(0, b'Good'), (1, b'Bad'), (2, b'Modified'), (3, b'Extra')])),
                ('exists', models.BooleanField(default=True)),
                ('value', models.TextField(null=True)),
                ('current_value', models.TextField(null=True)),
            ],
            options={
                'ordering': ('state', 'name'),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='interaction',
            name='confs',
            field=models.ManyToManyField(to='Reporting.ConfEntry'),
        ),
    ]
