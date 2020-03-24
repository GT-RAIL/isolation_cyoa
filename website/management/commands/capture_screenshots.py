#!/usr/bin/env python
# Capture screenshots from videos (Requires OpenCV)

import os
import sys
import cv2

from django.core.management.base import BaseCommand, CommandError

from dining_room import constants
from dining_room.models.domain import State, Transition, Suggestions


# Create the Command class

class Command(BaseCommand):
    """
    Capture screenshots of actions and transitions from the videos
    """

    help = "Capture screenshots from videos. Requires OpenCV (`pip install opencv-python`)"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
        videos_folder = os.path.join(os.getenv('HOME'), 'data/2019-12-09/videos')
        output_folder = os.path.join(os.getenv('HOME'), 'data/2019-12-09/screenshots')
        trajectory = constants.OPTIMAL_ACTION_SEQUENCES['kc.dt.default.default.default.empty.dt']

        # Start traversing the tree and grab images
        action, expected_values = trajectory[0]
        start_state = State(expected_values['server_state_tuple'])
        video = cv2.VideoCapture(os.path.join(videos_folder, expected_values['video_link']))

        # Print some stats
        num_frames  = video.get(cv2.CAP_PROP_FRAME_COUNT)
        video.set(cv2.CAP_PROP_POS_FRAMES, num_frames-1)
        _, img = video.read()
        print(img.shape)
        cv2.imwrite(os.path.join(output_folder, 'capture.png'), img)
        print("Done")
