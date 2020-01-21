# Generated by Django 3.0.2 on 2020-01-21 01:23

import dining_room.models.website
import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(max_length=150, unique=True, validators=[django.contrib.auth.validators.ASCIIUsernameValidator()], verbose_name='username')),
                ('unique_key', models.CharField(max_length=150, unique=True, verbose_name='unique_key')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('date_modified', models.DateTimeField(auto_now=True, verbose_name='date modified')),
                ('study_condition', models.IntegerField(blank=True, choices=[(None, '(Unknown)'), (0, 'Baseline'), (1, 'DX Only'), (2, 'AX Only'), (3, 'DX & AX')], null=True, verbose_name='study condition')),
                ('start_condition', models.CharField(blank=True, choices=[(None, '(Unknown)'), ('kc.kc.default.above_mug.default.empty.dt', 'At Counter Above Mug'), ('kc.kc.occluding.default.default.empty.dt', 'At Counter Occluding'), ('kc.kc.occluding.above_mug.default.empty.dt', 'At Counter Occluding Above Mug'), ('dt.kc.default.default.default.empty.kc', 'At Counter Mislocalized'), ('kc.dt.default.default.default.empty.dt', 'At Table'), ('kc.dt.default.above_mug.default.empty.dt', 'At Table Above Mug'), ('kc.dt.occluding.default.default.empty.dt', 'At Table Occluding'), ('kc.dt.occluding.above_mug.default.empty.dt', 'At Table Occluding Above Mug')], max_length=80, null=True, verbose_name='start condition')),
                ('scenario_completed', models.BooleanField(blank=True, default=None, null=True, verbose_name='scenario completed?')),
                ('date_started', models.DateTimeField(blank=True, null=True, verbose_name='date started')),
                ('date_finished', models.DateTimeField(blank=True, null=True, verbose_name='date finished')),
                ('age_group', models.IntegerField(blank=True, choices=[(0, 'Prefer Not To Say'), (1, '20 & below'), (2, '21 - 25'), (3, '26 - 30'), (4, '31 - 35'), (5, '36 - 40'), (6, '41 - 45'), (7, '46 - 50'), (8, '51 & over')], null=True)),
                ('robot_experience', models.IntegerField(blank=True, choices=[(0, 'Rarely Or Never'), (1, 'Approximately Twice A Year'), (2, 'Approximately Twice A Month'), (3, 'Approximately Twice A Week'), (4, 'Almost Everyday')], null=True, verbose_name='how often do you interact with robots?')),
                ('gender', models.CharField(blank=True, choices=[('U', 'Prefer Not To Say'), ('F', 'Female'), ('M', 'Male')], max_length=1, null=True)),
                ('date_demographics_completed', models.DateTimeField(blank=True, null=True, verbose_name='date demographics completed')),
                ('supposed_to_grab_bowl', models.BooleanField(blank=True, null=True, verbose_name="The robot's task is to grab the bowl?")),
                ('supposed_to_go_to_couch', models.BooleanField(blank=True, null=True, verbose_name="The robot's task is to take the object to the couch?")),
                ('will_view_in_third_person', models.BooleanField(blank=True, null=True, verbose_name='You will see live camera feeds of the robot in third person?')),
                ('will_be_able_to_hear_robot', models.BooleanField(blank=True, null=True, verbose_name='You will be able to hear the robot?')),
                ('long_time_to_recover', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='It took me a long time to help the robot recover')),
                ('easy_to_diagnose', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='It was easy to diagnose the error')),
                ('long_time_to_understand', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='It took me a long time to understand what was wrong with the robot')),
                ('system_helped_resume', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='The system helped me in assisting the robot')),
                ('easy_to_recover', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='It was easy to recover from the errors in the task')),
                ('system_helped_understand', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='The system helped me understand what went wrong with the robot')),
                ('comments', models.TextField(blank=True, null=True, verbose_name='Comments and Feedback')),
                ('date_survey_completed', models.DateTimeField(blank=True, null=True, verbose_name='date survey completed')),
                ('ignore_data_reason', models.TextField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', dining_room.models.website.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Demographics',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Demographics',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('dining_room.user',),
            managers=[
                ('objects', dining_room.models.website.UserManager()),
            ],
        ),
    ]
