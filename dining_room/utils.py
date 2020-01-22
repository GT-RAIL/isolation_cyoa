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
from django.core.files.base import File, ContentFile
from django.utils import timezone
from storages.backends.dropbox import DropBoxStorage, DropBoxStorageException


logger = logging.getLogger(__name__)


# Dealing with dropbox connections


class OverwriteDropboxStorage(DropBoxStorage):
    """
    Overwrite files when saving instead of the default add
    """

    def save(self, name, content, write_mode=dropbox.files.WriteMode.overwrite, mute=True):
        """
        Overwrite the default storage API that renames files. ``content`` is a
        django File object type or one of its subclasses
        """
        if name is None:
            name = content.name

        return self._save(name, content, write_mode, mute)

    def _save(self, name, content, write_mode, mute=True):
        """
        Given the name of the file and the content (django File object or its
        subclasses) overwrite the file if it exists

        If the incoming stream was a file, it is closed when the method returns
        """

        # Create a content file if the incoming data is not that
        if not hasattr(content, 'open'):
            content = ContentFile(content)

        content.open()
        if content.size <= self.CHUNK_SIZE:
            self.client.files_upload(content.read(), self._full_path(name), write_mode, mute=mute)
        else:
            self._chunked_upload(content, self._full_path, write_mode, mute)

        content.close()
        return name

    def _chunked_upload(self, content, dest_path, write_mode, mute=True):
        upload_session = self.client.files_upload_session_start(content.read(self.CHUNK_SIZE))
        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session.session_id, offset=content.tell())
        commit = dropbox.files.CommitInfo(path=dest_path, mode=write_mode, mute=mute)

        while content.tell() < content.size:
            if (content.size - content.tell()) <= self.CHUNK_SIZE:
                self.client.files_upload_session_finish(content.read(self.CHUNK_SIZE), cursor, commit)
            else:
                self.client.files_upload_session_append_v2(content.read(self.CHUNK_SIZE), cursor)
                cursor.offset = content.tell()


class DropboxConnection:
    """
    Helper to wrap the excellent utilities already provided by the Dropbox
    storage API
    """

    VIDEO_LINKS_FILE = 'data/video_links.csv'
    USERDATA_FOLDER = 'data/'

    # The fields in the user data
    USERDATA_CSV_HEADERS = [
        'timestamp', 'start_state', 'diagnoses', 'diagnosis_certainty', 'action', 'next_state',
        'video_loaded_time', 'video_stop_time', 'dx_selected_time', 'dx_confirmed_time', 'ax_selected_time'
    ]

    def __init__(self):
        # Set the userdata based on the settings (I don't think settings are
        # loaded when modules are imported?)
        self.USERDATA_FOLDER = os.path.join(
            DropboxConnection.USERDATA_FOLDER,
            'userdata_2020-01-20' if not settings.DEBUG else 'userdata_dev'
        )

        # Create the storage system
        self.storage = OverwriteDropboxStorage()

        # Cache some of the data so that we don't make too many requests
        self._video_links = None

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
        writer.writerows(csv_data)
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

        Returns the data (bytes) that was written to dropbox
        """
        csv_filename = os.path.join(self.USERDATA_FOLDER, user.csv_file)

        try:
            read_file = self.storage.open(csv_filename)
            experiment_data = self._get_csv_rows(read_file)
        except (dropbox.exceptions.ApiError, DropBoxStorageException) as e:
            experiment_data = [DropboxConnection.USERDATA_CSV_HEADERS]

        # If there is no incoming data (the user has restarted), then
        # create a dictionary. Otherwise, we set the timestamp field here
        if data is None or not isinstance(data, dict):
            data = { 'timestamp': timezone.now().timestamp() }
        else:
            data['timestamp'] = timezone.now().timestamp()

        row = []
        for header in DropboxConnection.USERDATA_CSV_HEADERS:
            # We specifically test here for equality to None
            row.append(data[header] if data.get(header) is not None else '')

        # Add the row to the CSV data
        experiment_data.append(row)

        # Write the data to dropbox
        write_data = self._set_csv_bytes(experiment_data)
        try:
            self.storage.save(csv_filename, write_data)
        except dropbox.exceptions.ApiError as e:
            logger.error(f"Error writing to Dropbox: {e}")
            write_data = None

        return write_data
