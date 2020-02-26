#!/usr/bin/env python
# Manage the data in the AMT CSV files

import os
import sys

from django.core.management.base import BaseCommand, CommandError

from dining_room.stats import data_loader


# Create the Command class

class Command(BaseCommand):
    """
    Create CSV files of the users that we can export
    """

    help = "Output CSV files of the user data"

    DEFAULT_FOLDER = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '../../../../data/2019-12-09/results'
    ))

    def add_arguments(self, parser):
        parser.add_argument('--output_folder', default=Command.DEFAULT_FOLDER)

    def handle(self, *args, **options):
        assert os.path.exists(options['output_folder']) and os.path.isdir(options['output_folder'])

        # Get the survey df
        survey_df = data_loader.get_survey_df()
        survey_df.to_csv(os.path.join(options['output_folder'], 'users.csv'))

        # Get the actions df
        actions_df = data_loader.get_actions_df()
        actions_df.to_csv(os.path.join(options['output_folder'], 'actions.csv'))

        self.stdout.write(self.style.SUCCESS("CSV data generated"))
