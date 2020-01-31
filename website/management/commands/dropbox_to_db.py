#!/usr/bin/env python
# Fetch JSON data from dropbox and load into the database

import os
import sys
import json
import pprint
import traceback

import dropbox

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from dining_room.models import User, StudyManagement


# Create the Command class

class Command(BaseCommand):
    """
    Dump the users and the associated mangement object that was used. Note that
    this does NOT preserve the StudyManagement links
    """

    help = "Load data from JSON files and put them in the DB. Does not preserve StudyManagement links"

    USER_DETAILS_FILE = 'user_details.json'
    MANAGEMENT_DETAILS_FILE = 'management.json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize a connection to dropbox
        self.dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)

    def add_arguments(self, parser):
        parser.add_argument('data_directory', help=f"The data directory in {os.path.join(settings.DROPBOX_ROOT_PATH, settings.DROPBOX_DATA_FOLDER)} to get the json files from")
        parser.add_argument('-i', '--ignore-duplicates', action="store_true")
        parser.add_argument('-c', '--confirm-duplicates', action='store_true', help="Confirm duplicates with human")

    def _download_dropbox(self, dbx_filename, local_filename):
        try:
            self.dbx.files_download_to_file(local_filename, dbx_filename)
        except dropbox.exceptions.ApiError as e:
            raise CommandError(f"Error downloading dropbox file: {e.user_message_text}")

    def handle(self, *args, **options):
        dbx_folder = os.path.join(settings.DROPBOX_ROOT_PATH, settings.DROPBOX_DATA_FOLDER, options['data_directory'])

        # Create a dictionary of files to create (and associated settings)
        fixtures_to_download = [
            (Command.MANAGEMENT_DETAILS_FILE, {
                'name': 'dining_room.StudyManagement',
                'model': StudyManagement
            }),
            (Command.USER_DETAILS_FILE, {
                'name': 'dining_room.User',
                'model': User,
                'ignore_fields': { 'groups', 'user_permissions', 'study_management' }
            }),
        ]

        # Loop through the fixtures to dump, and the settings to dump and
        # synchronize them with dropbox
        for filename, model_details in fixtures_to_download:
            # The user data is dumped and synchronized
            if options.get('verbosity') > 0:
                self.stdout.write(self.style.HTTP_INFO(f"Downloading {model_details['name']}"))

            local_filename = os.path.join('/tmp', filename)
            dbx_filename = os.path.join(dbx_folder, filename)
            self._download_dropbox(dbx_filename, local_filename)
            if not os.path.exists(local_filename):
                raise CommandError(f"Could not download {model_details['name']} to {local_filename}")

            if options.get('verbosity') > 1:
                self.stdout.write("Writing to database")

            with open(local_filename, 'r') as fd:
                data = json.load(fd)

            for row in data:
                # Try to save the data
                try:
                    data_dict = { k: v for k, v in row['fields'].items() if k not in model_details.get('ignore_fields', {}) }
                    item = model_details['model'](**data_dict)
                    item.save()
                    continue
                except Exception as e:
                    if not options.get('ignore_duplicates') and not options.get('confirm_duplicates'):
                        raise CommandError(f"Failure saving model: {e}\n{traceback.format_exc()}")
                    else:
                        self.stdout.write(f"Not writing row for model {row['model']} with pk {row['pk']}: {e}")
                        if options.get('confirm_duplicates'):
                            self.stdout.write('Should we update model (u), ignore (i), or error (e) out?')
                            response = ''
                            while response.lower() not in ['u', 'e', 'i']:
                                response = input('> ')

                            if response.lower() == 'e':
                                raise CommandError("Exiting, as directed")
                            elif response.lower() == 'i':
                                continue

                # If we're here, then update the data
                queryset = model_details['model'].objects.all()
                for field, value in data_dict.items():
                    new_queryset = queryset.filter(**{field: value})
                    if new_queryset.count() == 0:
                        continue

                    queryset = new_queryset
                    if queryset.count() == 1:
                        break

                if queryset.count() != 1:
                    raise CommandError("Could not find a suitable item to update in DB")

                item = queryset[0]
                for field, value in data_dict.items():
                    setattr(item, field, value)
                item.save()

            # Print complete
            if options.get('verbosity') > 0:
                self.stdout.write(self.style.SUCCESS(f"Synchronized {model_details['name']}"))
