# Generated by Django 3.2.14 on 2022-07-27 15:59

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import private_storage.fields
import private_storage.storage.files
import rehagoal_server_app.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='RehagoalUser',
            fields=[
                ('id', models.SlugField(default=rehagoal_server_app.models.pkgen, max_length=12, primary_key=True, serialize=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rehagoal_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SimpleUser',
            fields=[
            ],
            options={
                'verbose_name': 'BenutzerIn',
                'verbose_name_plural': 'BenutzerInnen',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.SlugField(default=rehagoal_server_app.models.pkgen, max_length=12, primary_key=True, serialize=False)),
                ('content', private_storage.fields.PrivateFileField(storage=private_storage.storage.files.PrivateFileSystemStorage(), upload_to=rehagoal_server_app.models.replace_filename)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rehagoal_server_app.rehagoaluser')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
