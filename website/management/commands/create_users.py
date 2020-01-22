#!/usr/bin/env python
# Create a test set of users

import os
import sys
import csv
import uuid

import dropbox

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist


# Fetch the default user model
User = get_user_model()


# Create the Command class

class Command(BaseCommand):
    help = "Given the number of users per condition, and the list of study and start conditions, create a CSV file of user details"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Infer the start and study conditions
        self.study_conditions = [
            x[0] for x in User.StudyConditions.choices
            if x[0] is not None
        ]
        self.study_conditions_display = dict(User.StudyConditions.choices)

        # TODO: This should be replaced with an automatic inference, as above
        self.start_conditions = [
            User.StartConditions.AT_COUNTER_ABOVE_MUG,
            User.StartConditions.AT_COUNTER_OCCLUDING,
            User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG,
            # User.StartConditions.AT_COUNTER_MISLOCALIZED,
            # User.StartConditions.AT_TABLE,
            # User.StartConditions.AT_TABLE_ABOVE_MUG,
            # User.StartConditions.AT_TABLE_OCCLUDING,
            # User.StartConditions.AT_TABLE_OCCLUDING_ABOVE_MUG,
        ]

        # Initialize a connection to dropbox
        self.dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)

    def add_arguments(self, parser):
        parser.add_argument('number_desired_users', type=int, help="The number of users per condition")
        parser.add_argument('-r', '--regenerate', action='store_true', help="Regenerate the list of users?")
        parser.add_argument('-f', '--filename', default=os.path.join('dropbox://', settings.DROPBOX_ROOT_PATH[1:], 'data/user_details.csv'), help="The file to store the data in")
        parser.add_argument('--no_check', action='store_true', help="Check that the user details match; if not, create/update the user")

    def _get_local_filename(self, filename):
        if filename.startswith('dropbox://'):
            local_filename = os.path.join('/tmp', os.path.basename(filename))
            try:
                self.dbx.files_download_to_file(local_filename, filename[len('dropbox:/'):])
            except dropbox.exceptions.ApiError as e:
                self.stdout.write(f"Error downloading dropbox file: {e.user_message_text}")
        else:
            local_filename = filename

        return local_filename

    def _synchronize_dropbox(self, filename, local_filename):
        if filename.startswith('dropbox://'):
            try:
                with open(local_filename, 'rb') as fd:
                    data = fd.read()
                    self.dbx.files_upload(data, filename[len('dropbox:/'):], dropbox.files.WriteMode.overwrite, mute=True)
            except dropbox.exceptions.ApiError as e:
                self.stdout.write(f"Error uploading dropbox file: {e.user_message_text}")
                filename = local_filename

        else:
            filename = local_filename

        return filename

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("Starting user generation"))

        # Get the local file
        filename = self._get_local_filename(options['filename'])

        number_desired_users = options['number_desired_users']
        user_details = []
        if not options.get('regenerate') and os.path.exists(filename):
            with open(filename, 'r') as fd:
                reader = csv.reader(fd)
                for details in reader:
                    user_details.append(details)

        if not options.get('no_check') and len(user_details) > 0:
            if options.get('verbosity') > 0:
                self.stdout.write("Checking (& updating) users in the DB")

            checked_user_details = []
            for detail in user_details:
                detail = self._check_user(detail, **options)
                checked_user_details.append(detail)

            user_details = checked_user_details

        if options.get('verbosity') > 0:
            self.stdout.write(f"Starting with {len(user_details)} users")

        for study_condition in self.study_conditions:
            for start_condition in self.start_conditions:
                # Get the number of users that already exist for the condition
                if not options.get('regenerate'):
                    number_existing_users = User.objects.filter(study_condition=study_condition, start_condition=start_condition).count()
                else:
                    number_existing_users = 0

                if options.get('verbosity') > 0:
                    self.stdout.write(f"{number_existing_users} -> {number_desired_users} for {self.study_conditions_display[study_condition]}, {start_condition}")

                for idx in range(number_existing_users, number_desired_users):
                    details = self._create_user(study_condition, start_condition, **options)
                    user_details.append(details)

        # Save the details
        with open(filename, 'w') as fd:
            writer = csv.writer(fd)
            for details in user_details:
                writer.writerow(details)

        # Synchronize with dropbox if necessary
        self._synchronize_dropbox(options['filename'], filename)

        # Print complete
        self.stdout.write(self.style.SUCCESS("User generation complete!"))

    def _create_user(self, study_condition, start_condition, username=None, unique_key=None, password=None, **options):
        """
        Create a random user with a username and password. Return the tuple of the
        username, password, and the unique_key
        """
        user = User(username=username or User.objects.make_random_password(allowed_chars='abcdefghjkmnpqrstuvwxyz23456789'),
                    unique_key=unique_key or User.objects.make_random_password(),
                    study_condition=study_condition,
                    start_condition=start_condition)
        password = password or uuid.uuid4()
        user.set_password(password)
        user.save()

        if options.get('verbosity') > 1:
            self.stdout.write(f"Created: {user.username}, {user.unique_key}")

        return user.username, user.unique_key, password, study_condition, start_condition

    def _check_user(self, details, **options):
        """
        Check that a user with the given details exists. If not create or update
        the user
        """
        username, unique_key, password, study_condition, start_condition = details
        try:
            user = User.objects.get(username=username)
            assert user.unique_key == unique_key, f"Unique Key: {user.unique_key} != {unique_key}"
            assert user.check_password(password), f"Password: != {password}"
            assert user.study_condition == study_condition, f"Study Condition: {user.study_condition} != {study_condition}"
            assert user.start_condition == start_condition, f"Start Condition: {user.start_condition} != {start_condition}"
        except ObjectDoesNotExist:
            details = self._create_user(study_condition, start_condition, username, unique_key, password, **options)
        except AssertionError as e:
            if options.get('verbosity') > 1:
                self.stdout.write(f"Mismatch: {e}")
            User.objects.filter(username=username).update(username=username, unique_key=unique_key, study_condition=study_condition, start_condition=start_condition)
            user.set_password(password)
            user.save()

        return details
