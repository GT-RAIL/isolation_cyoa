# Generated by Django 3.0.2 on 2020-01-31 01:40

import logging

import dining_room.models.website
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.contrib.auth.hashers import make_password
from dining_room.models import User as DRUser


logger = logging.getLogger(__name__)


def create_study_management(apps, schema_editor):
    """Create the single study management row"""
    start_conditions = [
        'kc.dt.default.default.default.empty.dt',
        'dt.kc.default.default.default.empty.kc',
        'kc.kc.default.above_mug.default.empty.dt',
        'kc.kc.occluding.default.default.empty.dt',
        'kc.kc.occluding.above_mug.default.empty.dt',
        'kc.dt.occluding.above_mug.default.empty.dt',
    ]

    StudyManagement = apps.get_model('dining_room', 'StudyManagement')
    sm = StudyManagement(data_directory='userdata_dev', enabled_start_conditions="\n".join(start_conditions))
    sm.save()


def remove_study_management(apps, schema_editor):
    """Remove all study management rows"""
    StudyManagement = apps.get_model('dining_room', 'StudyManagement')
    StudyManagement.objects.all().delete()


# Turns out we have to redo the model creation methods here because of migration
# philosophies
def create_user(User, username, password=None):
    password = password or username
    user = User(username=username, unique_key=username)
    user.password = make_password(password)
    user.save()
    return user


# Migrations for creating the superuser

def create_superuser(apps, schema_editor):
    """Create the superuser"""
    User = apps.get_model('dining_room', 'User')
    if User.objects.filter(username='banerjs').count() == 0:
        superuser = create_user(User, 'banerjs', 'IsolationCYOA')
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.study_condition = DRUser.StudyConditions.DXAX_100
        superuser.start_condition = DRUser.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG
        superuser.save()

def remove_superuser(apps, schema_editor):
    """Remove the superuser"""
    User = apps.get_model('dining_room', 'User')
    try:
        superuser = User.objects.get(username='banerjs')
        superuser.delete()
    except Exception as e:
        logger.error(f"Error in deleting superuser: {e}")
        # we don't actually care


# Define the list of workers to blacklist
BLACKLISTED_WORKER_IDS = [
    '\'\'',
    '1258',
    '25588',
    '256',
    '45',
    '56879',
    '586',
    'A1VR1XQEQQXYUE',
    'A1WPCXNFENBSY4',
    'A1ZZCIE79O3048',
    'A21SP7E5DFFX37',
    'A25YZ7RE911DPQ',
    'A2APG8MSLJ6G2K',
    'A2B153AHPWHLH1',
    'A2GRJVN7B5YR96',
    'A2O2Y99RA9GFUJ',
    'A2PXZ58VIBFNQQ',
    'A2XCEMBRPHIWEG',
    'A33VGSEJ44ORMF',
    'A3CH8O5PB3UKD7',
    'A3I62J5XYOY6C8',
    'A3OT6R8ZCGIQWD',
    'A3RLCGRXA34GC0',
    'A5TMU62U5FE5K',
    'A9LXSGXZM4IJE',
    'AL8TL480ET24G',
    'ASCLZFXD9WMON',
    'ATJ9VBARQEB46',
    'AU5BD5NSSES9H',
    'AUMTP6BXBDBXL',
    'AV22FQTJNBUZT',
    'fdgffghhgj',
    'fgfdhfghfgh',
    'sfdvsdgeu',
    'test_worker',
    'vjhgjhgjhk',
]


# Create the migration functions for blacklisting workers

def add_blacklisted_users(apps, schema_editor):
    """Add blacklisted users from worker ids"""
    User = apps.get_model('dining_room', 'User')
    for idx, worker_id in enumerate(BLACKLISTED_WORKER_IDS):
        # Check if the user exists. If so, blacklist them. Else add them as a
        # blacklisted user
        found_workers = User.objects.filter(amt_worker_id=worker_id)
        if found_workers.count() > 0:
            for widx, worker in enumerate(found_workers):
                worker.username = f'blacklist{idx}_{widx}'
                worker.ignore_data_reason = 'BLACKLIST\n' + (worker.ignore_data_reason or '')
                worker.save()
        else:
            user = create_user(User, f'blacklist{idx}')
            user.amt_worker_id = worker_id
            user.ignore_data_reason = 'BLACKLIST\n' + (user.ignore_data_reason or '')
            user.save()


def remove_blacklisted_users(apps, schema_editor):
    """Remove all users with a blacklist username"""
    User = apps.get_model('dining_room', 'User')
    blacklisted_users = User.objects.filter(username__istartswith='blacklist')
    for user in blacklisted_users:
        try:
            user.delete()
        except Exception as e:
            logger.error(f"Error in deleting blacklisted user: {e}")
            # we don't actually care


# Register the migration

class Migration(migrations.Migration):

    dependencies = [
        ('dining_room', '0002_auto_20200212_2210'),
    ]

    operations = [
        migrations.RunPython(create_study_management, remove_study_management),
        migrations.RunPython(create_superuser, remove_superuser),
        migrations.RunPython(add_blacklisted_users, remove_blacklisted_users),
    ]
