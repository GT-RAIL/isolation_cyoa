#!/usr/bin/env python
# Common utility classes and methods

import os
import io
import csv
import time
import datetime
import codecs
import logging

import dropbox

import numpy as np

from django.conf import settings
from django.utils import timezone
from storages.backends.dropbox import DropBoxStorage, DropBoxStorageException


logger = logging.getLogger(__name__)


# The Dropbox connection class

class DropboxConnection:
    """
    Helper to wrap the excellent utilities already provided by the Dropbox
    storage API
    """

    VIDEO_LINKS_FILE = 'data/video_links.csv'
    USERDATA_FOLDER = 'data'

    # The fields in the user data
    USERDATA_CSV_HEADERS = [
        'timestamp', 'start_state', 'action', 'diagnosis'
    ]

    def __init__(self):
        self.storage = DropBoxStorage()

        # Cache some of the data so that we don't make too many requests
        _video_links = None

    def _get_csv_rows(self, read_file):
        """Given a DropBoxFile, try to read it as a CSV and return the rows.
        The read file will be closed after this method is called"""
        reader = csv.reader(codecs.iterdecode(read_file, 'utf-8'))
        links_data = []
        for row in reader:
            links_data.append(row)

        read_file.close()
        return links_data

    def _set_csv_bytes(self, csv_data):
        """Given CSV data as list of lists, convert to bytes that can be written
        to a file. Return the bytes"""
        sio = io.StringIO()
        writer = csv.writer(sio)
        writer.writerows(sio)
        return codecs.encode(sio.getvalue(), 'utf-8')

    @property
    def video_links(self):
        """A dictionary of video name -> video CORS enabled link"""
        if self._video_links is not None:
            return self._video_links

        # Get the links file from dropbox
        links_file = self.storage.open(DropboxConnection.VIDEO_LINKS_FILE)
        links_data = self._get_csv_rows(links_file)

        # Create the links dictionary
        self._video_links = { l[0]: l[-1] for l in links_data }
        return self._video_links

    def write_to_csv(self, user, **data):
        """
        Given a dictionary of data, write it to the users's CSV. An empty
        dictionary is added automatically as a restart marker with a timestamp
        of now()
        """
        csv_filename = os.path.join(DropboxConnection.USERDATA_FOLDER, user.csv_file)

        try:
            read_file = self.storage.open(csv_filename)
            experiment_data = self._get_csv_rows(read_file)
        except DropBoxStorageException as e:
            experiment_data = [DropboxConnection.USERDATA_CSV_HEADERS]

        # If there is no incoming data (the user has restarted), then
        # automatically populate the timestamp
        if data is None or len(data) == 0 or data.get('timestamp') is None:
            data = { 'timestamp': timezone.now() }

        row = []
        for header in DropboxConnection.USERDATA_CSV_HEADERS:
            row.append(data.get(header, ''))

        # Add the row to the CSV data
        experiment_data.append(row)

        # Write the data to dropbox
        write_data = self._set_csv_bytes(experiment_data)
        # TODO: Figure out how to write the data to dropbox. Also, test if
        # we can save the same file multiple times. Probably not? In which case
        # we need to override the storages Storage to do overwrites
