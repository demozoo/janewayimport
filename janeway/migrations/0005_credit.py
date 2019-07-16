# Generated by Django 2.1.5 on 2019-07-11 11:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('janeway', '0004_releasetype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('janeway_id', models.IntegerField()),
                ('category', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='janeway.Name')),
                ('release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='janeway.Release')),
            ],
        ),
    ]