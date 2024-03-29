# Generated by Django 2.1.5 on 2019-01-27 18:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('janeway', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('since', models.DateField(blank=True, null=True)),
                ('until', models.DateField(blank=True, null=True)),
                ('founder', models.BooleanField(default=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_memberships', to='janeway.Author')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to='janeway.Author')),
            ],
        ),
    ]
