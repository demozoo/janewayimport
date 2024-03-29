# Generated by Django 2.1.5 on 2019-07-17 22:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('janeway', '0008_downloadlink'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packed_in', to='janeway.Release')),
                ('pack', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pack_contents', to='janeway.Release')),
            ],
        ),
    ]
