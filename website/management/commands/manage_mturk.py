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
from django.db.models import Q

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
    BATCH_OUTPUT_HEADERS = [
        "HITId",
        "HITTypeId",
        "Title",
        "AssignmentId",
        "WorkerId",
        "Answer.surveycode",
        "Approve",
        "Reject",
    ]

    UPDATE_QUALIFICATIONS_HEADERS = [
        "WorkerId",
        "UPDATE-{qualification}",
    ]
    QUALIFICATION_NAME = "Assisted Robot"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize a connection to dropbox
        self.dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)

    def add_arguments(self, parser):
        parser.add_argument('dropbox_folder', help="The data directory on dropbox to get the CSV files from")
        parser.add_argument('--output-folder', default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')), help="Folder to output generated CSV to")
        parser.add_argument('--qualification', default=Command.QUALIFICATION_NAME, help="The qualification to update")

    def _find_batch_results_files(self, dbx_folder):
        filenames = []
        try:
            results = self.dbx.files_list_folder(dbx_folder)
            for entry in results.entries:
                if Command.BATCH_RESULTS_FILE_RE.match(entry.name) is not None:
                    filenames.append(entry.path_display)
        except dropbox.exceptions.ApiError as e:
            raise CommandError(f"Error listing filenames in folder {dbx_folder}: {e}")

        return filenames

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

    def handle(self, *args, **options):
        # raise CommandError("This command remains incomplete")
        verbosity = options.get('verbosity')
        dbx_folder = os.path.join(settings.DROPBOX_ROOT_PATH, settings.DROPBOX_DATA_FOLDER, options['dropbox_folder'])
        dbx_batch_filenames = self._find_batch_results_files(dbx_folder)
        batch_csv_data = { filename: self._get_csv_data(filename) for filename in dbx_batch_filenames }

        encountered_ids = set()

        for filename, file_data in batch_csv_data.items():
            if verbosity > 1:
                self.stdout.write(f"Parsing {filename}")

            # Parse out the files into dataframes
            batch_df = pd.DataFrame(file_data)

            # First we update the accept / reject
            for idx, work in batch_df.iterrows():
                worker_id = work['WorkerId'].strip()
                surveycode = work['Answer.surveycode'].strip()

                # Check to see that we haven't seen this worker in the CSV
                if worker_id in encountered_ids:
                    batch_df.loc[idx, 'Reject'] = 'Cannot submit on multiple HITs'
                    self.stdout.write(f"Rejecting {worker_id} in {os.path.basename}. Found multiple times")
                    continue

                try:
                    _ = User.objects.get(
                        Q(unique_key=surveycode) &
                        Q(amt_worker_id=worker_id) &
                        (Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason='')) &
                        Q(is_staff=False)
                    )
                    batch_df.loc[idx, 'Approve'] = 'x'
                except (exceptions.ObjectDoesNotExist, exceptions.MultipleObjectsReturned):
                    batch_df.loc[idx, 'Reject'] = 'Cannot match worker id to survey code'
                    self.stdout.write(f"Rejecting {worker_id} in {os.path.basename(filename)}. Code: {surveycode}")

            # Save the CSV data
            batch_df[Command.BATCH_OUTPUT_HEADERS].to_csv(
                os.path.join(options['output_folder'], os.path.basename(filename)),
                index=False
            )

        # Create an update to the qualifications. For this we use ALL users
        qualifications_to_update = []
        headers = [x.format(**options) for x in Command.UPDATE_QUALIFICATIONS_HEADERS]

        for user in User.objects.all():
            if user.amt_worker_id is not None:
                qualifications_to_update.append({
                    headers[0]: user.amt_worker_id,
                    headers[1]: 1,
                })

        # Write out the CSV
        qualifications_to_update = pd.DataFrame(qualifications_to_update)
        qualifications_to_update[headers].to_csv(os.path.join(options['output_folder'], 'qualifications.csv'), index=False)

        self.stdout.write(self.style.SUCCESS("CSV generated!"))
