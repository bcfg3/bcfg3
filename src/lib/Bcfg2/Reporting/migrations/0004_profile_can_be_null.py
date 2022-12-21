# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Reporting', '0003_expand_hash_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interaction',
            name='profile',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='Reporting.Group', null=True),
            preserve_default=True,
        ),
    ]
