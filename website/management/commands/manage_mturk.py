#!/usr/bin/env python
# Manage the data in the AMT CSV files

import os
import sys
import csv
import json
import re
import tempfile
import codecs

import dropbox

import numpy as np
import pandas as pd

from django.conf import settings
from django.core import management, exceptions
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from dining_room.models import User, StudyManagement


# Create the Command class

class Command(BaseCommand):
    """
    Parse an MTurk CSV and approve/reject work based on the codes that are in
    the CSV. Also output a CSV to update worker qualifications
    """

    help = "Parse MTurk CSV files to approve work and to update worker qualifications"

    BATCH_RESULTS_FILE_FORMAT = 'Batch_{batch_number}_batch_results.csv'
    BATCH_RESULTS_FILE_RE = re.compile(r'Batch_(?P<batch_number>\d+)_batch_results\.csv')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize a connection to dropbox
        self.dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)

    def add_arguments(self, parser):
        sm = StudyManagement.get_default()
        parser.add_argument('--output-folder', default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')), help="Folder to output generated CSV to")
        parser.add_argument('--dropbox-folder', default=sm.data_directory, help="The data directory on dropbox to get the CSV files from")

    def _find_batch_results_file(self, dbx_folder):
        try:
            results = self.dbx.files_list_folder(dx_folder)
            for entry in results.entries:
                if

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
            raise CommandError(f"Error downloading dropbox file: {e.user_message_text}")

        return data

    def handle(self, *args, **options):
        # raise CommandError("This command remains incomplete")

        dbx_folder = os.path.join(settings.DROPBOX_ROOT_PATH, settings.DROPBOX_DATA_FOLDER, options['dropbox_folder'])
        local_folder = '/tmp'

        # Fetch the files locally
        batch_filename = Command.BATCH_RESULTS_FILE_FORMAT.format(**options)
        self._download_dropbox(os.path.join(dbx_folder, batch_filename), os.path.join(local_folder, batch_filename))

        # Parse out the files into dataframes
        batch_df = pd.read_csv(os.path.join(local_folder, batch_filename))

        # First we update the accept / reject
        worker_statuses = []
        for work in batch_df.loc.iterrows():
            try:
                _ = User.objects.get(unique_key=work['Answer.surveycode'].strip())
            except (exceptions.ObjectDoesNotExist, exceptions.MultipleObjectsReturned):
                # TODO
                worker_statuses
