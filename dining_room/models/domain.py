#!/usr/bin/env python
# The file to handle CYOA in the Dining Room domain (described in `tw` and in
# the Overview slides)

import os
import sys
import copy
import logging
import collections

import numpy as np

from .. import constants


logger = logging.getLogger(__name__)


# Helper functions and classes

# Included here because we might need to use this module as a standalone in a
# docker container on the webserver

def display(string):
    """Given a location or object or action string, get the display name"""
    return " ".join([x.capitalize() for x in string.split('_')])


def get_location_from_action_name(action):
    """Return the location from the name of the action"""
    if action.startswith('at_'):
        location_name = action[len('at_'):]
    elif action.startswith('go_to_'):
        location_name = action[len('go_to_'):]
    elif action.startswith('look_at_'):
        location_name = action[len('look_at_'):]
    else:
        location_name = None

    return location_name


def get_object_from_action_name(action):
    """Return the object from the name of the action"""
    if action.startswith('pick_'):
        object_name = action[len('pick_'):]
    else:
        object_name = None

    return object_name


# The main classes

class State:
    """
    Encapsulates the state of the scenario with the following attributes:

        - the location of the robot base (true location) - kc (default), dt, c
        - the location of the objects (true location) - kc (expected default), dt
        - the state of the jug - default, occluding, gripper (out of view)
        - the state of the bowl - default, above_mug, gripper (out of view)
        - the state of the mug - default, gripper (in view)
        - object in the gripper - empty, jug, bowl, mug
        - the current label for the dining table - dt (default), kc (induced), c

    Based on these attributes, other attributes can be inferred (using methods
    and dynamic properties). These include:

        - the label of the current location
        - the objects that the robot "sees"
        - the actions that the robot can take (IMPORTANT). This is returned as
            the set of ``Transition`` that are applicable at the given state

    In the UI, the ``State`` determines:

        - the text the user sees after a video has played
        - the transitions that the user can make based on helpers from
            ``Transition``. These will be presented as actions to the user
        - if the user is done with the session

    Once a state is initialized, subsequent states are dynamically created.
    """

    # Attributes (private). Use getters and setters instead
    _base_location = None
    _object_location = None
    _jug_state = None
    _bowl_state = None
    _mug_state = None
    _gripper_state = None
    _current_dt_label = None

    def __init__(self, state):
        """
        Given a 7 tuple of the state, create a State object
        """
        if isinstance(state, (list, tuple,)):
            assert len(state) == 7
            self.tuple = state
        elif isinstance(state, State):
            self.tuple = state.tuple
        else:
            raise NotImplementedError("Unknown type: {}".format(state))

    def __eq__(self, other):
        return isinstance(other, State) and (self.tuple == other.tuple)

    def __ne__(self, other):
        if not isinstance(other, State):
            return NotImplemented
        else:
            return not self.__eq__(other)

    def __hash__(self):
        return hash(self.tuple)

    def __str__(self):
        return str((
            constants.LOCATION_NAMES[self.base_location],
            constants.LOCATION_NAMES[self.object_location],
            self.jug_state,
            self.bowl_state,
            self.mug_state,
            self.gripper_state,
            self.relocalized_base_location,
        ))

    def __repr__(self):
        return str(self.tuple)

    # Attributes
    @property
    def base_location(self):
        """The true location of the robot base"""
        return self._base_location

    @base_location.setter
    def base_location(self, value):
        assert value in constants.LOCATIONS, value
        self._base_location = value

    @property
    def object_location(self):
        """The true location of the objects"""
        return self._object_location

    @object_location.setter
    def object_location(self, value):
        assert value in constants.LOCATIONS[:-1], value
        self._object_location = value

    @property
    def jug_state(self):
        """The state of the jug"""
        return self._jug_state

    @jug_state.setter
    def jug_state(self, value):
        assert value in constants.OBJECT_STATES['jug'], value
        self._jug_state = value

    @property
    def bowl_state(self):
        """The state of the bowl"""
        return self._bowl_state

    @bowl_state.setter
    def bowl_state(self, value):
        assert value in constants.OBJECT_STATES['bowl'], value
        self._bowl_state = value

    @property
    def mug_state(self):
        """The state of the mug"""
        return self._mug_state

    @mug_state.setter
    def mug_state(self, value):
        assert value in constants.OBJECT_STATES['mug'], value
        self._mug_state = value

    @property
    def gripper_state(self):
        """The state of the gripper"""
        return self._gripper_state

    @gripper_state.setter
    def gripper_state(self, value):
        assert value is None or value in (constants.OBJECTS + [constants.EMPTY_GRIPPER]), value
        self._gripper_state = value or constants.EMPTY_GRIPPER

    @property
    def current_dt_label(self):
        """
        The current mapping of the dining table; used to look up localization
        """
        return self._current_dt_label

    @current_dt_label.setter
    def current_dt_label(self, value):
        assert value in constants.LOCATIONS, value
        self._current_dt_label = value

    # Inferred attributes
    @property
    def tuple(self):
        """A tuple representation of the state"""
        return (
            self.base_location,
            self.object_location,
            self.jug_state,
            self.bowl_state,
            self.mug_state,
            self.gripper_state,
            self.current_dt_label,
        )

    @tuple.setter
    def tuple(self, value):
        assert len(value) == len(self.tuple), value
        self.base_location, self.object_location, self.jug_state, self.bowl_state, self.mug_state, self.gripper_state, self.current_dt_label = value

    @property
    def relocalized_base_location(self):
        """The label of the robot's current location"""
        current_location = constants.LOCATION_NAMES[self.base_location]
        dt_mapping = constants.LOCATION_NAMES[self.current_dt_label]
        relocalized_base_location = constants.LOCATION_MAPPINGS['dining_table_to_' + dt_mapping][current_location]
        return relocalized_base_location

    @property
    def mislocalized(self):
        """Is the robot mislocalized?"""
        return (self.current_dt_label != 'dt')

    @property
    def gripper_empty(self):
        """Is the robot's gripper empty?"""
        return self.gripper_state == constants.EMPTY_GRIPPER

    @property
    def visible_objects(self):
        """The objects that are 'visible' to the robot"""
        visible_objects = []
        if self.base_location == self.object_location:
            if self.jug_state != 'gripper' and not (self.mug_state == 'gripper' and self.object_location == 'dt'):
                visible_objects.append('jug')

            if self.bowl_state != 'gripper' and not (self.mug_state == 'gripper' and self.object_location == 'kc' and self.jug_state == 'gripper'):
                visible_objects.append('bowl')

            if self.mug_state == 'default' and self.jug_state != 'occluding':
                visible_objects.append('mug')

        return visible_objects

    @property
    def graspable_objects(self):
        """The objects that the robot can pick up given the state"""
        graspable_objects = []
        if self.gripper_empty and self.base_location == self.object_location:
            # Cache the visible objects
            visible_objects = self.visible_objects

            if 'jug' in visible_objects:
                graspable_objects.append('jug')

            if 'bowl' in visible_objects and (self.jug_state != 'occluding' or self.bowl_state != 'above_mug'):
                graspable_objects.append('bowl')

            if 'mug' in visible_objects and self.bowl_state != 'above_mug':
                graspable_objects.append('mug')

        return graspable_objects

    @property
    def is_end_state(self):
        """Return True if this is an end state; else return False"""
        return (
            self.base_location == 'c'
            and self.mug_state == 'gripper'
            and self.gripper_state == 'mug'
            and self.current_dt_label == 'dt'
        )

    # Methods on states
    def get_valid_actions(self):
        """
        The valid actions that are applicable in this state. Return a dictionary
        of the actions in constants.ACTIONS associated with a boolean true or
        false value
        """
        actions_valid_check = {}

        # Iterate through the actions and add to the transitions dictionary if
        # the action is applicable
        for action in constants.ACTIONS.keys():

            # First, if this is a valid transition, then by all means add it to
            # the list of things that the person can do
            end_state = Transition.get_end_state(self, action)
            if end_state is not None:
                actions_valid_check[action] = True
                continue

            # But, if it isn't a valid transition, check to see if the state of
            # the robot would change (we know some hard coded conditions), so
            # update the list of actions based on that
            location_name, object_name = get_location_from_action_name(action), get_object_from_action_name(action)

            if object_name is not None and object_name in self.visible_objects and self.gripper_empty:
                actions_valid_check[action] = True
                continue

            # Otherwise, the action is invalid here
            actions_valid_check[action] = False

        # Return the computed transitions
        return actions_valid_check


class Transition:
    """
    Encapsulates a move from one state to another using an action. It has the
    following attributes:

        - the start state
        - the action name
        - the resulting state

    From these attributes, other inferred attributes & methods are:

        - the name of the video corresponding to the transition
        - whether the arm is in motion during the transition
        - checking the validity of a possible transition

    In the UI, the ``Transition`` determines:

        - the video that is played when the user selects an action
        - the text that is displayed during the transition (arm motion...?)

    Once a state is provided, we create valid transitions automatically &
    dynamically from that state using methods in the `State` class
    """

    _start_state = None
    _action = None
    _end_state = None

    def __init__(self, start_state, action, end_state):
        self.start_state = start_state
        self.action = action
        self.end_state = end_state

    def __eq__(self, other):
        return isinstance(other, Transition) and (self.tuple == other.tuple)

    def __ne__(self, other):
        if not isinstance(other, Transition):
            return NotImplemented
        else:
            return not self.__eq__(other)

    def __hash__(self):
        return hash(self.tuple)

    def __str__(self):
        return str((self.start_state, constants.ACTIONS.get(self.action, self.action), self.end_state))

    def __repr__(self):
        return repr(self.tuple)

    # Attributes
    @property
    def start_state(self):
        """The state that this transition starts at. None if this is the start"""
        return self._start_state

    @start_state.setter
    def start_state(self, value):
        assert isinstance(value, State) or value is None, value
        self._start_state = value

    @property
    def action(self):
        """The label of the action"""
        return self._action

    @action.setter
    def action(self, value):
        assert value in constants.ACTIONS.keys() or value is None, value
        self._action = value

    @property
    def end_state(self):
        """The end state of the transition"""
        return self._end_state

    @end_state.setter
    def end_state(self, value):
        assert isinstance(value, State), value
        self._end_state = value

    # Inferred attributes
    @property
    def tuple(self):
        """A tuple representation of the transition"""
        return (
            self.start_state.tuple if self.start_state is not None else None,
            self.action,
            self.end_state.tuple,
        )

    @property
    def arm_status(self):
        """Return if the arm is in motion or not"""
        return constants.ARM_STATUS[int(self.action is not None and (self.action.startswith('pick_') or self.action == 'place'))]

    @property
    def video_name(self):
        """The name of the video file to use"""
        # If this is the start, then we should be using the end state to
        # determine the video name. Else use the start state
        action = self.action
        if self.start_state is None and self.action is None:
            state = self.end_state
            action = 'noop'
        else:
            state = self.start_state

        # Test the equality of the state to the end state; if equal, this is a
        # noop, unless the equality is a result of the look_at_ action
        if (state == self.end_state and not action.startswith('look_at_')):
            action = 'noop'

        # The action is also a noop if it is a localization change
        if action.startswith('at_'):
            action = 'noop'

        # Then update look_at_ and go_to_ action definitions based on the
        # localization params
        if action.startswith('look_at_') or action.startswith('go_to_'):
            if action.startswith('look_at_'):
                action_type = 'look_at_'
                location_name = action[len('look_at_'):]
            else:
                action_type = 'go_to_'
                location_name = action[len('go_to_'):]

            location_name = constants.LOCATION_NAMES[location_name]
            dt_mapping = constants.LOCATION_MAPPINGS['dining_table_to_' + constants.LOCATION_NAMES[state.current_dt_label]]
            desired_location = { v: k for k, v in dt_mapping.items() }[location_name]
            desired_location = constants.LOCATION_NAMES[desired_location]

            # If we are going to be repeating the location, then the action is a
            # noop. Else, we should have a video for the case
            if desired_location == state.base_location:
                action = 'noop'
            else:
                action = action_type + desired_location

        # Create another variable to manipulate now based on the videos that we
        # did collect
        video_action = action

        # Then, reuse the look_at_ actions if they are the reusable type
        if state.base_location == 'kc' and video_action == 'look_at_c':
            video_action = 'look_at_dt'
        elif state.base_location == 'c' and video_action == 'look_at_dt':
            video_action = 'look_at_kc'

        # Then reuse the singular videos that don't look at the objects
        object_location = state.object_location
        jug_state, bowl_state, mug_state = state.jug_state, state.bowl_state, state.mug_state
        gripper_state = state.gripper_state

        # The robot is at the couch and is looking at the couch with nothing in
        # its hand
        if state.base_location == 'c' and video_action == 'noop' and mug_state != 'gripper':
            object_location = 'kc'
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at the couch and is looking at the couch with the mug in
        # its hand
        elif state.base_location == 'c' and video_action == 'noop' and mug_state == 'gripper':
            object_location = 'kc'
            jug_state, bowl_state, mug_state = 'gripper', 'gripper', 'gripper'

        # The robot is at DT and the objects are at KC, but the robot is doing
        # a noop action
        elif state.base_location == 'dt' and object_location == 'kc' and video_action == 'noop' and mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at KC and the objects are at DT, but the robot is doing
        # a noop action
        elif state.base_location == 'kc' and object_location == 'dt' and video_action == 'noop' and mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at DT and the objects are at KC, and the robot is going
        # to look at the couch
        elif state.base_location == 'dt' and object_location == 'kc' and video_action == 'look_at_c' and mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at DT and the objects are at KC, and the robot is going
        # to navigate to the couch
        elif state.base_location == 'dt' and object_location == 'kc' and video_action == 'go_to_c' and mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at the couch, the objects are at KC, but the robot is
        # navigating to DT
        elif state.base_location == 'c' and object_location == 'kc' and video_action == 'go_to_dt':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at KC, the objects are at DT, and the robot is
        # navigating to the couch
        elif state.base_location == 'kc' and object_location == 'dt' and video_action == 'go_to_c' and mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        # The robot is at DT, all the objects have been picked up, then reuse
        # the videos from the kc picks
        elif object_location == 'dt' and (jug_state == bowl_state == mug_state == 'gripper'):
            object_location = 'kc'

        # Convert the video name to assume an empty gripper unless the gripper
        # is not empty, it is not the mug, and the action is not noop
        if mug_state == 'gripper' or video_action != 'noop' or state.gripper_empty:
            gripper_state = constants.EMPTY_GRIPPER

        return "{state.base_location}.{object_location}.{jug_state}.{bowl_state}.{mug_state}.{video_action}.{gripper_state}.mp4".format(**locals())

    # Methods
    @staticmethod
    def get_end_state(state, action):
        """
        Given a state and an action, get the end state that should result from
        them. If the action is not applicable in this state, return None
        """
        # First we check to see if the action is applicable in the state
        end_state = None

        # Cache some of the attributes
        relocalized_base_location = state.relocalized_base_location
        graspable_objects = state.graspable_objects

        # Get some attributes about the action
        location_name, object_name = get_location_from_action_name(action), get_object_from_action_name(action)

        # Do not allow a place if the gripper is empty or if the mug is in there
        if (state.gripper_empty or state.gripper_state == 'mug') and action == 'place':
            return end_state

        # Do not allow a move or look action if we have something in the gripper
        if not state.gripper_empty and state.gripper_state != 'mug' and (action.startswith('go_to_') or action.startswith('look_at_')):
            return end_state

        # Do not allow a pick of an object if it is not graspable
        if object_name is not None and object_name not in graspable_objects:
            return end_state

        # Do not allow anything that is not localization if we are at the couch
        # with the mug but we are mislocalized
        if state.base_location == 'c' and state.current_dt_label != 'dt' and state.mug_state == 'gripper' and not action.startswith('at_'):
            return end_state

        # Then we use custom rules to update the state according to the action
        end_state = State(state)

        # Idempotent mappings of AT(X), GOTO(X), LOOK_AT(X) if we are at X
        # (according to the localization) are allowed
        if location_name is not None and constants.LOCATION_NAMES[location_name] == relocalized_base_location:
            return end_state

        # Update the localization
        elif action.startswith('at_'):
            base_location = constants.LOCATION_NAMES[state.base_location]
            location_name = constants.LOCATION_NAMES[location_name]

            # Find the appropriate mapping and set the end state to that
            for mapping_name, mapping in constants.LOCATION_MAPPINGS.items():
                if mapping[base_location] == location_name:
                    end_state.current_dt_label = constants.LOCATION_NAMES[mapping['dining_table']]
                    break

        # Update the robot's position
        elif action.startswith('go_to_'):
            dt_mapping = constants.LOCATION_MAPPINGS['dining_table_to_' + constants.LOCATION_NAMES[state.current_dt_label]]
            location_name = constants.LOCATION_NAMES[location_name]
            desired_location = { v: k for k,v in dt_mapping.items() }[location_name]
            desired_location = constants.LOCATION_NAMES[desired_location]
            end_state.base_location = desired_location

        # Look at does nothing to the state itself
        elif action.startswith('look_at_'):
            pass

        # Update the object states based on the objects that are picked
        elif action.startswith('pick_'):
            end_state.gripper_state = object_name
            setattr(end_state, object_name + '_state', 'gripper')

        # Update the object states based on the object that was picked
        elif action == 'place':
            end_state.gripper_state = constants.EMPTY_GRIPPER

        # If this is a restart of the camera, pretend as if that has happened
        elif action == 'restart_video':
            pass

        # Something has gone wrong; fail the action
        else:
            logger.debug(f"Unknown action: {action}. Failed")
            end_state = None

        # Return the result
        return end_state


class Suggestions:
    """
    A class to provide suggestions. It can be initialized with a maximum number
    of suggestions, and whether to pad the suggestions on output. On the website
    these configs can be obtained from the user / study management object
    """

    DEFAULT_MAX_DX_SUGGESTIONS = 1
    DEFAULT_MAX_AX_SUGGESTIONS = 1
    DEFAULT_PAD_SUGGESTIONS = False
    DEFAULT_NOISE_LEVEL = 0

    # Parameters that we cannot change
    DEFAULT_RNG_SEED = 0x1337
    RNG_STATE_SAVE_MODULO = int(1e5)

    DX_CORRUPT_IDX_OFFSETS = [1, 4, 8]
    AX_CORRUPT_IDX_OFFSETS = [1, 4, 8]

    def __init__(self,
        user=None,
        max_dx_suggestions=DEFAULT_MAX_DX_SUGGESTIONS,
        max_ax_suggestions=DEFAULT_MAX_AX_SUGGESTIONS,
        pad_suggestions=DEFAULT_PAD_SUGGESTIONS,
        noise_level=DEFAULT_NOISE_LEVEL,
        show_dx_suggestions=True,
        show_ax_suggestions=True,
        *args, **kwargs
    ):
        """
        Create this suggestions provider object. If instantiated with a user,
        then we infer the properties of the suggestions to provide from the user
        object; else we use parameters passed explicitly to the __init__ method.
        The initialization from the user object takes precedence.
        """
        self.user = user if user is not None and user.is_authenticated else None
        use_defaults = (user is None or not user.is_authenticated)

        self.max_dx_suggestions = max_dx_suggestions if use_defaults else user.study_management.max_dx_suggestions
        self.max_ax_suggestions = max_ax_suggestions if use_defaults else user.study_management.max_ax_suggestions
        self.pad_suggestions = pad_suggestions if use_defaults else user.study_management.pad_suggestions
        self.noise_level = noise_level if use_defaults else user.noise_level

        self.show_dx_suggestions = True if use_defaults else user.show_dx_suggestions
        self.show_ax_suggestions = True if use_defaults else user.show_ax_suggestions

        # Create an rng
        self.rng = np.random.default_rng(Suggestions.DEFAULT_RNG_SEED if use_defaults else user.rng_state)

    @staticmethod
    def get_next_rng_seed(rng):
        """Given an rng, get the seed that should be used the next time the rng
        is reinitialized from scratch"""
        return rng.bit_generator.state['state']['state'] % Suggestions.RNG_STATE_SAVE_MODULO

    def optimal_action(self, state, action):
        """
        Suggest the optimal action to take given the state of the system. This
        is done based on heuristics

        Args:
          state (State) : the state that the user is in; never None
          action (str)  : the action the user took; None if no action yet

        Returns:
          suggestions (list of str) : the suggestions appropriate to the condition
              represented by the function
        """
        suggestions = []

        # If we've completed the scenario, then don't suggest anything
        if state.is_end_state:
            pass

        # Check to see if we are mislocalized; if so, fix that
        elif state.mislocalized:
            suggestions.append(f'at_{state.base_location}')

        # Check to see if we have the mug in our hand, if so, go to the couch
        elif state.gripper_state == 'mug' and state.base_location != 'c':
            suggestions.append('go_to_c')

        # Check to see if the gripper is not empty
        elif not state.gripper_empty:
            suggestions.append('place')

        # Check to see if we can see the mug and it is pickup-able
        elif 'mug' in state.graspable_objects:
            suggestions.append('pick_mug')

        # Check to see if we can pick up the bowl
        elif 'bowl' in state.graspable_objects and 'mug' in state.visible_objects:
            suggestions.append('pick_bowl')

        # Check to see if we can pick up the jug
        elif 'jug' in state.graspable_objects:
            suggestions.append('pick_jug')

        # Check to see if we're in the same location as the objects
        elif state.base_location != state.object_location:
            suggestions.append(f'go_to_{state.object_location}')

        # Return the suggestions
        return suggestions

    def ordered_diagnoses(self, state, action, accumulate=False):
        """
        Suggest diagnoses based on the following priority order:
        - lost (mislocalized)
        - different_location
        - cannot_see
        - cannot_pick
        - none

        If accumulate is set to True, then multiple suggestions of diagnoses are
        returned

        Args:
          state (State) : the state that the user is in; never None
          action (str)  : the action the user took; None if no action yet

        Returns:
          suggestions (list of str) : the suggestions appropriate to the condition
              represented by the function
        """
        suggestions = []

        # An expression to check if we should return multiple diagnoses
        ac_check = lambda x: (len(x) == 0 or accumulate)

        # Check to see if the state is mislocalized
        if ac_check(suggestions) and state.mislocalized:
            suggestions.append('lost')

        # Check to see if we might need to go to a different location
        if ac_check(suggestions) and state.object_location == 'dt' and state.base_location == 'kc':
            suggestions.append('different_location')

        # Check to see if the problem is that we cannot see the mug (and that
        # we're not actually holding it)
        if ac_check(suggestions) and 'mug' not in state.visible_objects and state.gripper_state != 'mug':
            suggestions.append('cannot_see')

        # Check to see if the problem is that we cannot grasp the mug (and that
        # we're not actually holding it). We need to recreate the logic for
        # graspable_objects here in order the bypass the empty gripper test that
        # is there
        if (
            ac_check(suggestions) and
            ('mug' not in state.visible_objects or state.bowl_state == 'above_mug') and
            state.gripper_state != 'mug'
        ):
            suggestions.append('cannot_pick')

        # If there is no other suggestion, then we don't think anything is wrong
        if len(suggestions) == 0:
            suggestions.append('none')

        # Return the suggestions
        return suggestions

    def _should_corrupt(self, offsets):
        """
        Decide if the user's suggestions should be corrupted based on a
        deterministic paradigm
        """
        if self.user is not None:
            num_noise_offsets = int(self.noise_level * 10)
            offsets = [offsets[i] for i in range(num_noise_offsets)]
            should_corrupt = any([
                ((self.user.number_state_requests - offset) % 10 == 0)
                for offset in offsets
            ])
        else:
            should_corrupt = bool(self.rng.choice(2))

        return should_corrupt

    def _add_noise_and_pad(self, suggestions, alternatives, *, should_corrupt=False, number=None):
        """
        Depending on the noise level, substitute elements in suggestions with
        those from the alternatives. If number is provided, then pad elements
        of alternatives into suggestions until we equal number.

        - len(alternatives) MUST be > len(suggestions)
        - no element in suggestions should be in alternatives
        """
        number = number or len(suggestions)

        # Check if we need to corrupt the data & corrupt if so
        if should_corrupt:
            suggestions = self.rng.choice(alternatives, size=len(suggestions), replace=False).tolist()

        # If we need to pad, then pad
        alternatives = set(alternatives) - set(suggestions)
        while len(suggestions) < number:
            # We don't want to cause an exception when we pad the suggestions,
            # so just catch an exception if that's the case and exit
            try:
                suggestions.append(self.rng.choice(list(sorted(alternatives))))
                alternatives.discard(suggestions[-1])
            except:
                logger.error(f"Exception padding suggestions: {e}")
                break

        return suggestions

    def suggest_dx(self, state, action):
        """
        Given the state and action, return diagnosis suggestions. This function
        calls the appropriate methods in this class depending on how the class
        has been configured.

        Args:
          state (State) : the state that the user is in; never None
          action (str)  : the action the user took; None if no action yet

        Returns:
          suggestions (list of str) : the suggestions
        """
        if self.show_dx_suggestions:
            suggestions = self.ordered_diagnoses(state, action, accumulate=True)
        else:
            suggestions = []

        # Limit the number to the maximum number of diagnoses
        limited_suggestions = suggestions[:self.max_dx_suggestions]

        # Alternative suggestions
        alternatives = [x for x in constants.DIAGNOSES.keys() if x not in suggestions]

        # Add noise and pad. We pad if there is no problem as well
        suggestions = self._add_noise_and_pad(
            limited_suggestions,
            alternatives,
            should_corrupt=self._should_corrupt(Suggestions.DX_CORRUPT_IDX_OFFSETS),
            number=self.max_dx_suggestions if self.pad_suggestions else None
        )

        # Update the user's rng state
        if self.user is not None:
            self.user.rng_state = Suggestions.get_next_rng_seed(self.rng)
            self.user.save()

        # Return the diagnoses
        return suggestions

    def suggest_ax(self, state, action):
        """
        Given the state and action, return diagnosis suggestions. This function
        calls the appropriate methods in this class depending on how the class
        has been configured.

        Args:
          state (State) : the state that the user is in; never None
          action (str)  : the action the user took; None if no action yet

        Returns:
          suggestions (list of str) : the suggestions
        """
        if self.show_ax_suggestions:
            suggestions = self.optimal_action(state, action)
        else:
            suggestions = []

        # Limit the number to the maximum number of diagnoses
        limited_suggestions = suggestions[:self.max_ax_suggestions]

        # Alternative suggestions. We don't treat SA actions separately
        valid_actions_check = state.get_valid_actions()
        alternatives = [k for k, v in valid_actions_check.items() if (k not in suggestions and v)]

        # Add noise and pad
        suggestions = self._add_noise_and_pad(
            limited_suggestions,
            alternatives,
            should_corrupt=self._should_corrupt(Suggestions.AX_CORRUPT_IDX_OFFSETS),
            number=self.max_ax_suggestions if self.pad_suggestions else None
        )

        # Update the user's rng state
        if self.user is not None:
            self.user.rng_state = Suggestions.get_next_rng_seed(self.rng)
            self.user.save()

        # Return the actions
        return suggestions
