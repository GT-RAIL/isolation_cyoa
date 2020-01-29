#!/usr/bin/env python
# Dump the data as JSON to the dropbox folder specified by the StudyManagement

import os
import sys
import json

import dropbox

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from dining_room.models import User, StudyManagement


# Create the Command class

class Command(BaseCommand):
    """
    Dump the users and the associated mangement object that was used
    """

    help = "Upload JSON files to dropbox with the details of the users as well as the management command that was used to generate them"

    USER_DETAILS_FILE = 'user_details.json'
    MANAGEMENT_DETAILS_FILE = 'management.json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize a connection to dropbox
        self.dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)

    def add_arguments(self, parser):
        sm = StudyManagement.get_default()
        parser.add_argument('--dropbox-folder', default=sm.data_directory, help="The data directory on dropbox to send the CSV files to")

    def _synchronize_dropbox(self, dbx_filename, local_filename):
        try:
            with open(local_filename, 'rb') as fd:
                data = fd.read()
                self.dbx.files_upload(data, dbx_filename, dropbox.files.WriteMode.overwrite, mute=True)
        except dropbox.exceptions.ApiError as e:
            raise CommandError(f"Error uploading dropbox file: {e.user_message_text}")

    def handle(self, *args, **options):
        dbx_folder = os.path.join(settings.DROPBOX_ROOT_PATH, settings.DROPBOX_DATA_FOLDER, options['dropbox_folder'])

        # Create a dictionary of files to create (and associated settings)
        fixtures_to_upload = {
            Command.USER_DETAILS_FILE: {
                'model': 'dining_room.User',
            },
            Command.MANAGEMENT_DETAILS_FILE: {
                'model': 'dining_room.StudyManagement',
                # 'kwargs': { 'pks': str(sm.pk) },
            },
        }

        # Loop through the fixtures to dump, and the settings to dump and
        # synchronize them with dropbox
        for filename, model_details in fixtures_to_upload.items():
            # The user data is dumped and synchronized
            if options.get('verbosity') > 0:
                self.stdout.write(self.style.HTTP_INFO(f"Dumping {model_details['model']}"))

            local_filename = os.path.join('/tmp', filename)
            management.call_command('dumpdata',
                                    model_details['model'],
                                    all=True,
                                    format='json',
                                    output=local_filename,
                                    verbosity=0,
                                    **model_details.get('kwargs', {}))
            if not os.path.exists(local_filename):
                raise CommandError(f"Could not dump {model_details['model']} to {local_filename}")

            if options.get('verbosity') > 1:
                self.stdout.write("Uploading to Dropbox")

            dbx_filename = os.path.join(dbx_folder, filename)
            self._synchronize_dropbox(dbx_filename, local_filename)

            # Print complete
            if options.get('verbosity') > 0:
                self.stdout.write(self.style.SUCCESS(f"Synchronized {model_details['model']}"))
