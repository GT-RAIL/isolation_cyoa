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
        parser.add_argument('--videos-folder', default=os.path.join(os.getenv('HOME'), 'data/2019-12-09/videos'))
        parser.add_argument('--output-folder', default=os.path.join(os.getenv('HOME'), 'data/2019-12-09/screenshots'))
        parser.add_argument('--start-states', nargs='+', default=[
            'kc.dt.default.default.default.empty.dt',
            'dt.kc.default.default.default.empty.kc',
            'kc.kc.occluding.default.default.empty.dt',
            'kc.dt.occluding.above_mug.default.empty.dt',
        ])

    def _capture_from_video(self, name, video_file, output_folder, get_mid=True):
        # Since we don't check for the end in this traversal, just don't try
        # to get a video if the video does not exist
        if not os.path.exists(video_file):
            return

        video = cv2.VideoCapture(video_file)
        num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)

        # If we have more than X frames, get an intermediate frame
        if num_frames > 600 and get_mid:
            video.set(cv2.CAP_PROP_POS_FRAMES, num_frames // 2)
            _, img = video.read()
            cv2.imwrite(os.path.join(output_folder, f"{name}.mid.png"), img)

        # Capture the last frame and save it
        video.set(cv2.CAP_PROP_POS_FRAMES, num_frames-1)
        _, img = video.read()
        cv2.imwrite(os.path.join(output_folder, f"{name}.png"), img)

    def _get_shots(self, prefix, trajectory, videos_folder, output_folder):
        # First get the main sequence
        transitions_captured = set()
        for idx, (action, expected_values) in enumerate(trajectory):
            self._capture_from_video(
                f"{prefix}_{idx}",
                os.path.join(videos_folder, expected_values['video_link']),
                output_folder
            )
            transitions_captured.add(expected_values['video_link'])

        # Then get the alternatives at each state
        for idx, (action, expected_values) in enumerate(trajectory):
            state = State(expected_values['server_state_tuple'])
            self._traverse_tree(f"{prefix}_{idx}", state, videos_folder, output_folder, transitions_captured, depth=3)

    def _traverse_tree(self, prefix, state, videos_folder, output_folder, transitions_captured, depth=3):
        # We have reached the max depth
        if depth == 0:
            return

        # Iterate over the actions and get the next state
        applicable_actions = state.get_valid_actions()
        for action, valid in applicable_actions.items():
            if not valid or action in ['at_c', 'at_dt', 'at_kc', 'remove_obstacle', 'out_of_collision', 'restart_video', 'find_charger']:
                continue

            # Get the next state and the video to get to the state
            next_state = Transition.get_end_state(state, action)
            if next_state is None:
                continue

            transition = Transition(state, action, next_state)
            video_name = transition.video_name
            if not os.path.exists(os.path.join(videos_folder, video_name)):
                continue

            # If we have this video, then don't do anything
            if video_name in transitions_captured or 'noop' in video_name:
                continue

            # Capture the screenshot
            self._capture_from_video(
                f"{prefix}_{depth}_{action}",
                os.path.join(videos_folder, video_name),
                output_folder,
                get_mid=(action.startswith('look_at_'))
            )
            transitions_captured.add(video_name)

            # Traverse the tree
            self._traverse_tree(prefix, next_state, videos_folder, output_folder, transitions_captured, depth-1)

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
        videos_folder = options['videos_folder']
        output_folder = options['output_folder']

        # Iterate through the start states and get the sequences
        for idx, start_state in enumerate(options['start_states']):
            self.stdout.write(f"Generating shots for {start_state}")

            trajectory = constants.OPTIMAL_ACTION_SEQUENCES[start_state]
            self._get_shots(str(idx), trajectory, videos_folder, output_folder)

