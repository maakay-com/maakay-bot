# Generated by Django 3.2.7 on 2021-09-15 14:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maakay', '0006_auto_20210914_1010'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='maakayuser',
            name='total_lost_in_challenges',
        ),
    ]