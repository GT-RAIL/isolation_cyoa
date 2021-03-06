# Generated by Django 3.0.2 on 2020-01-28 16:06

import dining_room.models.website
import django.contrib.auth.validators
from django.db import migrations, models
from django.conf import settings


# Custom data migrations

# Autogenerated migration

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyManagement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled_study_conditions', models.PositiveIntegerField(default=0, help_text='A bit vector for the study conditions that are enabled')),
                ('enabled_start_conditions', models.TextField(default='none', help_text='\\n separated start conditions')),
                ('number_per_condition', models.PositiveIntegerField(default=0, help_text='Number of people per combination of the conditions')),
                ('max_number_of_people', models.PositiveIntegerField(default=0, help_text='Maximum number of people to provision IDs for')),
                ('data_directory', models.CharField(help_text="Data directory for user data within '/DiningRoom_IsolationCYOA/data'", max_length=20)),
            ],
            options={
                'verbose_name': 'study management',
                'verbose_name_plural': 'study management',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(max_length=30, unique=True, validators=[django.contrib.auth.validators.ASCIIUsernameValidator()], verbose_name='username')),
                ('unique_key', models.CharField(max_length=30, unique=True, verbose_name='unique_key')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('date_modified', models.DateTimeField(auto_now=True, verbose_name='date modified')),
                ('study_condition', models.IntegerField(blank=True, choices=[(None, '(Unknown)'), (1, 'Baseline'), (2, 'DX, 100'), (3, 'AX, 100'), (4, 'DX & AX, 100'), (5, 'DX, 90'), (6, 'AX, 90'), (7, 'DX & AX, 90'), (8, 'DX, 80'), (9, 'AX, 80'), (10, 'DX & AX, 80'), (11, 'DX, 70'), (12, 'AX, 70'), (13, 'DX & AX, 70')], null=True, verbose_name='study condition')),
                ('start_condition', models.CharField(blank=True, choices=[(None, '(Unknown)'), ('kc.kc.default.above_mug.default.empty.dt', 'At Counter Above Mug'), ('kc.kc.occluding.default.default.empty.dt', 'At Counter Occluding'), ('kc.kc.occluding.above_mug.default.empty.dt', 'At Counter Occluding Above Mug'), ('dt.kc.default.default.default.empty.kc', 'At Counter Mislocalized'), ('kc.dt.default.default.default.empty.dt', 'At Table'), ('kc.dt.default.above_mug.default.empty.dt', 'At Table Above Mug'), ('kc.dt.occluding.default.default.empty.dt', 'At Table Occluding'), ('kc.dt.occluding.above_mug.default.empty.dt', 'At Table Occluding Above Mug')], max_length=80, null=True, verbose_name='start condition')),
                ('scenario_completed', models.BooleanField(blank=True, default=None, null=True, verbose_name='scenario completed?')),
                ('date_started', models.DateTimeField(blank=True, null=True, verbose_name='date started')),
                ('date_finished', models.DateTimeField(blank=True, null=True, verbose_name='date finished')),
                ('age_group', models.IntegerField(blank=True, choices=[(0, 'Prefer Not To Say'), (1, '20 & below'), (2, '21 - 25'), (3, '26 - 30'), (4, '31 - 35'), (5, '36 - 40'), (6, '41 - 45'), (7, '46 - 50'), (8, '51 & over')], null=True)),
                ('gender', models.CharField(blank=True, choices=[('F', 'Female'), ('M', 'Male'), ('U', 'Other / Prefer Not to Say')], max_length=1, null=True)),
                ('robot_experience', models.IntegerField(blank=True, choices=[(0, 'Rarely Or Never'), (1, '1 - 3 Times a Year'), (2, 'Monthly'), (3, 'Weekly'), (4, 'Daily')], null=True, verbose_name='how often do you interact with robots?')),
                ('date_demographics_completed', models.DateTimeField(blank=True, null=True, verbose_name='date demographics completed')),
                ('supposed_to_grab_bowl', models.BooleanField(blank=True, null=True, verbose_name="The robot's goal is to pick up the Bowl?")),
                ('supposed_to_go_to_couch', models.BooleanField(blank=True, null=True, verbose_name="The robot's goal is to end up at the Couch?")),
                ('will_view_in_first_person', models.BooleanField(blank=True, null=True, verbose_name="You will see a first-person view from the robot's camera?")),
                ('supposed_to_select_only_one_error', models.BooleanField(blank=True, null=True, verbose_name='Even if there are multiple problems stopping the robot reaching its goal, you may only select one problem?')),
                ('actions_involve_invisible_arm_motion', models.BooleanField(blank=True, null=True, verbose_name='Some actions might involve robot arm motions that are not visible on the camera?')),
                ('number_incorrect_knowledge_reviews', models.IntegerField(default=0)),
                ('certain_of_actions', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='I was always certain of the actions that I was taking.')),
                ('not_sure_how_to_help', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='I was not always sure how to help the robot with the problems that I identified.')),
                ('system_helped_understand', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='The system helped me understand what went wrong with the robot.')),
                ('could_not_identify_problems', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name="I could not always identify the problems affecting the robot's ability to achieve its goal.")),
                ('information_was_enough', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='The amount of information presented to me was sufficient to easily diagnose problems.')),
                ('identify_problems_in_future', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='I am certain that in the future I will be able to easily identify problems using this system, and help the robot overcome them.')),
                ('system_was_responsible', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name="The system was largely responsible in helping me identify and address problems with the robot's tasks.")),
                ('rely_on_system_in_future', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='I would rely on this system to assist the robot in the event of future problems with its tasks.')),
                ('user_was_competent', models.IntegerField(blank=True, choices=[(0, 'Strongly Disagree'), (1, 'Disagree'), (2, 'Neutral'), (3, 'Agree'), (4, 'Strongly Agree')], null=True, verbose_name='I think that I was a competent user of the system during the study.')),
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
        migrations.CreateModel(
            name='Survey',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Surveys',
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
