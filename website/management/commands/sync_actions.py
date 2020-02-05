#!/usr/bin/env python
# Synchronize the actions from dropbox to the actions in the database

import os
import sys
import csv
import codecs
import pytz
import datetime
import tempfile
import traceback

import dropbox

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError

from dining_room.models import User, StudyManagement, StudyAction


# Create the Command class

class Command(BaseCommand):
    """
    Fetch the actions data from dropbox and load actions for the user
    """

    help = "Load actions data from dropbox and put them on the server"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize a connection to dropbox
        self.dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)

    def add_arguments(self, parser):
        parser.add_argument("--user-ids", nargs='*', default=[x.pk for x in User.objects.order_by('pk')], help="The user ids to get actions for")
        parser.add_argument("--raise-on-missing", action="store_true", help="Raise an error if the actions CSV file is missing")
        parser.add_argument("--raise-on-delete", action="store_true", help="Raise an error if there already exist actions for the user")
        parser.add_argument("--raise-no-actions", action="store_true", help="Raise an error if there are no actions in the CSV file")

    def _get_csv_data(self, dbx_filename):
        try:
            metadata, response = self.dbx.files_download(dbx_filename)

            data = []
            with tempfile.NamedTemporaryFile(suffix='.csv') as fd:
                fd.write(response.content)
                fd.seek(0)
                reader = csv.DictReader(codecs.iterdecode(fd, 'utf-8'))
                for row in reader:
                    data.append(row)

        except dropbox.exceptions.ApiError as e:
            raise CommandError(f"Error downloading dropbox file: {e}")

        return data

    def _check_data_exists(self, dbx_filename):
        try:
            return bool(self.dbx.files_get_metadata(dbx_filename))
        except dropbox.exceptions.ApiError:
            return False

    def _get_action_from_rows(self, current_row, previous_row=None):
        # Check to see if this is a terminating record; terminate if so
        current_row = dict(current_row)
        if previous_row is None or not current_row.get('start_state'):
            return None

        previous_row = dict(previous_row)

        # Convert the data to an action. We assume UTC timezone for now
        action = StudyAction()
        action.start_timestamp = datetime.datetime.fromtimestamp(float(previous_row['timestamp']), pytz.utc)
        action.end_timestamp = datetime.datetime.fromtimestamp(float(current_row['timestamp']), pytz.utc)

        # Set the attributes
        current_row.pop('timestamp', None)
        for key, value in current_row.items():
            if '_time' in key:
                setattr(action, key, datetime.datetime.fromtimestamp(float(value), pytz.utc))
            elif key == 'diagnoses':
                setattr(action, key, eval(value))
            else:
                setattr(action, key, value)

        # Return the action
        return action

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
        users = User.objects.filter(pk__in=options['user_ids'])

        # Iterate through the users and get their data
        for user in users:

            # Don't get anything for users that don't have associated folders
            if user.study_management is None:
                if verbosity > 0:
                    self.stdout.write(f"No management for {user}; skipping")
                continue

            # Remove existing actions for the user, if they exist
            if user.num_actions > 0:
                msg = f"{user.num_actions} actions exist for {user}"
                if options['raise_on_delete']:
                    raise CommandError(msg)
                else:
                    if verbosity > 1:
                        self.stdout.write(f"{msg}; removing")
                    user.studyaction_set.all().delete()

            # Construct the filename
            filename = os.path.join(settings.DROPBOX_ROOT_PATH, user.study_management.resolved_data_directory, user.csv_file)

            # Check to see if the data exists
            if not self._check_data_exists(filename):
                msg = f"CSV file missing for {user}"
                if options['raise_on_missing']:
                    raise CommandError(msg)
                else:
                    if verbosity > 0:
                        self.stdout.write(f"{msg}; skipping")
                    continue

            # Get the user's data
            csv_data = self._get_csv_data(filename)
            csv_len = len(csv_data)

            # Iterate and add actions to the model
            actions_added = []
            for idx, data in enumerate(reversed(csv_data)):
                prev_idx = (csv_len-idx-1) - 1
                action = self._get_action_from_rows(data, (csv_data[prev_idx] if prev_idx >= 0 else None))

                if action is None:
                    # Check to see if the last row was empty, and we should
                    # error on that. Else, just notify
                    if len(actions_added) == 0:
                        msg = f"There are no actions on file for {user}"
                        if options['raise_no_actions']:
                            raise CommandError(msg)
                        else:
                            if verbosity > 1:
                                self.stdout.write(f"{msg}; skipping")

                    # This is the last action we care about; we ignore
                    # everything before this
                    break
                else:
                    action.user = user
                    action.save()

            # Print a status message
            if verbosity > 0:
                self.stdout.write(f"Updated actions for {user}")

        # Print a completion message
        self.stdout.write(self.style.SUCCESS("Actions synchronized!"))
