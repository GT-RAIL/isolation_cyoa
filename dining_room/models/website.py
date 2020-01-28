import os
import csv
import dropbox

from django.conf import settings
from django.db import models
from django.contrib import auth
from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin, BaseUserManager)
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.utils import timezone
from django.utils.crypto import get_random_string, salted_hmac
from django.utils.translation import gettext_lazy as _

from .domain import State, Transition, constants


# Create the model for the user and the associated manager

class UserManager(models.Manager):
    """
    A custom manager that removes the tight coupling to email that's present in
    the base user manager.
    """

    use_in_migrations = True

    def make_random_password(self, length=10,
                             allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                           'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                           '23456789'):
        """
        Generate a random password with the given length and given
        allowed_chars. The default value of allowed_chars does not have "I" or
        "O" or letters and digits that look similar -- just to avoid confusion.
        """
        return get_random_string(length, allowed_chars)

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def _create_user(self, username, unique_key, password, **extra_fields):
        """
        Create and save a user with the given username, unique_key, and password
        """
        if not username:
            raise ValueError("Username must be set")
        username = self.model.normalize_username(username)
        user = self.model(username=username, unique_key=unique_key, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, unique_key, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        password = username
        extra_fields.pop('password', None)
        return self._create_user(username, unique_key, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        """"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('study_condition', User.StudyConditions.DX_AX)
        extra_fields.setdefault('start_condition', User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

        unique_key = username
        extra_fields.pop('unique_key', None)
        return self._create_user(username, unique_key, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        """Return a list of users with permissions"""
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            assert len(backends) == 1, f"Expected 1 backend, got: {backends}"
            backend, _ = backends[0]
        elif not isinstance(backend, str):
            raise TypeError(f"backend must be a dotted import path string. got {backend}")
        else:
            backend = auth.load_backend(backend)

        if hasattr(backend, 'with_perm'):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):
    """
    The custom user class that we create. The changes from the default
    definition are:

    1. We have a specific unique_key instead of an email, that can be used by
        MTurk workers to get compensation. We pretend the
    2. Demographic information about the user, their responses to questions, the
        condition, etc. are all recorded as part of the user field (to limit the
        number of rows)
    """

    # User Auth
    username_validator = ASCIIUsernameValidator()

    username = models.CharField(_('username'), max_length=30, unique=True, validators=[username_validator])
    unique_key = models.CharField(_('unique_key'), max_length=30, unique=True)

    # Permissions, etc.
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True) # Used in default User
    date_modified = models.DateTimeField(_('date modified'), auto_now=True)

    # Study condition tracking
    class StudyConditions(models.IntegerChoices):
        """The study conditions"""
        BASELINE = 1, _('Baseline')
        DX_ONLY = 2, _('DX Only')
        AX_ONLY = 3, _('AX Only')
        DX_AX = 4, _('DX & AX')
        # TODO: Add the actions with SA improvement conditions
        # TODO: Add the noise conditions
        __empty__ = _('(Unknown)')

    study_condition = models.IntegerField(_('study condition'), blank=True, null=True, choices=StudyConditions.choices)

    SHOW_DX_STUDY_CONDITIONS = [
        StudyConditions.DX_ONLY,
        StudyConditions.DX_AX,
    ]
    SHOW_AX_STUDY_CONDITIONS = [
        StudyConditions.AX_ONLY,
        StudyConditions.DX_AX,
    ]

    class StartConditions(models.TextChoices):
        """
        The start conditions. Given by the state description in domain.State
        """
        AT_COUNTER_ABOVE_MUG = 'kc.kc.default.above_mug.default.empty.dt'
        AT_COUNTER_OCCLUDING = 'kc.kc.occluding.default.default.empty.dt'
        AT_COUNTER_OCCLUDING_ABOVE_MUG = 'kc.kc.occluding.above_mug.default.empty.dt'
        AT_COUNTER_MISLOCALIZED = 'dt.kc.default.default.default.empty.kc'
        AT_TABLE = 'kc.dt.default.default.default.empty.dt'
        AT_TABLE_ABOVE_MUG = 'kc.dt.default.above_mug.default.empty.dt'
        AT_TABLE_OCCLUDING = 'kc.dt.occluding.default.default.empty.dt'
        AT_TABLE_OCCLUDING_ABOVE_MUG = 'kc.dt.occluding.above_mug.default.empty.dt'

        __empty__ = _('(Unknown)')

    start_condition = models.CharField(_('start condition'), max_length=80, blank=True, null=True, choices=StartConditions.choices)
    scenario_completed = models.BooleanField(_('scenario completed?'), blank=True, null=True, default=None)
    date_started = models.DateTimeField(_('date started'), blank=True, null=True)   # Starting the scenario
    date_finished = models.DateTimeField(_('date finished'), blank=True, null=True) # Not necessarily completed the scenario

    # Demographics
    class AgeGroups(models.IntegerChoices):
        PREFER_NOT_TO_SAY = 0
        BELOW_20  = 1, _("20 & below")
        BTW_20_25 = 2, _("21 - 25")
        BTW_25_30 = 3, _("26 - 30")
        BTW_30_35 = 4, _("31 - 35")
        BTW_35_40 = 5, _("36 - 40")
        BTW_40_45 = 6, _("41 - 45")
        BTW_45_50 = 7, _("46 - 50")
        ABOVE_50  = 8, _("51 & over")

    class Genders(models.TextChoices):
        FEMALE = 'F'
        MALE = 'M'
        PREFER_NOT_TO_SAY = 'U', _("Other / Prefer Not to Say")  # Unknown

    class RobotExperienceGroups(models.IntegerChoices):
        RARELY_OR_NEVER = 0
        ONE_TO_THREE_TIMES_A_YEAR = 1, _("1 - 3 Times a Year")
        MONTHLY = 2
        WEEKLY = 3
        DAILY = 4

    age_group = models.IntegerField(choices=AgeGroups.choices, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Genders.choices, blank=True, null=True)
    robot_experience = models.IntegerField(_("how often do you interact with robots?"), choices=RobotExperienceGroups.choices, blank=True, null=True)
    date_demographics_completed = models.DateTimeField(_('date demographics completed'), blank=True, null=True)

    # The knowledge review questions
    supposed_to_grab_bowl = models.BooleanField(_("The robot's goal is to pick up the Bowl?"), blank=True, null=True)
    supposed_to_go_to_couch = models.BooleanField(_("The robot's goal is to end up at the Couch?"), blank=True, null=True)
    will_view_in_first_person = models.BooleanField(_("You will see a first-person view from the robot's camera?"), blank=True, null=True)
    supposed_to_select_only_one_error = models.BooleanField(_("Even if there are multiple problems stopping the robot reaching its goal, you may only select one problem?"), blank=True, null=True)
    actions_involve_invisible_arm_motion = models.BooleanField(_("Some actions might involve robot arm motions that are not visible on the camera?"), blank=True, null=True)
    number_incorrect_knowledge_reviews = models.IntegerField(default=0)

    ACCEPTABLE_REVIEW_ANSWERS = [
        ('supposed_to_grab_bowl', False),
        ('supposed_to_go_to_couch', True),
        ('will_view_in_first_person', True),
        ('supposed_to_select_only_one_error', False),
        ('actions_involve_invisible_arm_motion', True),
    ]

    # Likert Responses
    class LikertResponses(models.IntegerChoices):
        STRONGLY_DISAGREE = 0
        DISAGREE = 1
        NEUTRAL = 2
        AGREE = 3
        STRONGLY_AGREE = 4

    certain_of_actions = models.IntegerField(
        _("I was always certain of the actions that I was taking."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    not_sure_how_to_help = models.IntegerField(
        _("I was not always sure how to help the robot with the problems that I identified."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    system_helped_understand = models.IntegerField(
        _("The system helped me understand what went wrong with the robot."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    could_not_identify_problems = models.IntegerField(
        _("I could not always identify the problems affecting the robot's ability to achieve its goal."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    information_was_enough = models.IntegerField(
        _("The amount of information presented to me was sufficient to easily diagnose problems."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    identify_problems_in_future = models.IntegerField(
        _("I am certain that in the future I will be able to easily identify problems using this system, and help the robot overcome them."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    system_was_responsible = models.IntegerField(
        _("The system was largely responsible in helping me identify and address problems with the robot's tasks."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    rely_on_system_in_future = models.IntegerField(
        _("I would rely on this system to assist the robot in the event of future problems with its tasks."),
        blank=True, null=True, choices=LikertResponses.choices
    )
    user_was_competent = models.IntegerField(
        _("I think that I was a competent user of the system during the study."),
        blank=True, null=True, choices=LikertResponses.choices
    )

    comments = models.TextField(_("Comments and Feedback"), blank=True, null=True)
    date_survey_completed = models.DateTimeField(_('date survey completed'), blank=True, null=True)

    # Field to ignore the user's data in the event of an error
    ignore_data_reason = models.TextField(blank=True, null=True)

    # Required constants
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'unique_key'  # Just in case some code actually uses it
    REQUIRED_FIELDS = ['unique_key']

    # Associate the manager and the meta information
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    # Inferred properties that are used by the code to figure out how to render
    # the UI for the user

    @property
    def csv_file(self):
        """The CSV file associated with the user's actions"""
        return f"{self.username.lower()}.csv"

    @property
    def show_dx_suggestions(self):
        """Return a boolean if the user should see diagnosis suggestions"""
        return self.study_condition in User.SHOW_DX_STUDY_CONDITIONS

    @property
    def show_ax_suggestions(self):
        """Return a boolean if the user should see action suggestions"""
        return self.study_condition in User.SHOW_AX_STUDY_CONDITIONS

    @property
    def study_progress(self):
        """
        The progress the user has made through the study. These are str
        constants in the domain and are primarily used to decide the pages the
        user is allowed to view
        """
        state = None
        if self.last_login is None:
            state = 'CREATED'
        elif self.date_demographics_completed is None:
            state = 'LOGGED_IN'
        elif self.date_started is None:
            state = 'DEMOGRAPHED'
        elif self.date_finished is None:
            state = 'STARTED'
        elif self.date_survey_completed is None:
            state = 'FINISHED'
        elif self.date_survey_completed is not None:
            state = 'SURVEYED'

        return state

    @property
    def invalid_data(self):
        """
        The data for this user is invalid if there is a reason to ignore
        their data
        """
        return (self.ignore_data_reason is not None)

    # Custom methods
    def reset_progress(self, *args, **kwargs):
        """
        Reset the state of the user. Accepts the same arguments as save
        """
        self.date_demographics_completed = self.date_started = self.date_finished = self.date_survey_completed = None
        self.save(*args, **kwargs)
        return self

    def reset_invalid_data(self, *args, **kwargs):
        """
        Reset the invalid data state of the user. Accepts the same arguments as
        save
        """
        self.ignore_data_reason = None
        self.save(*args, **kwargs)
        return self


# Model for managing the study condition

class StudyManagement(models.Model):
    """
    This model manages how new users are assigned to study conditions
    """

    enabled_study_conditions = models.PositiveIntegerField(default=0, help_text="A bit vector for the study conditions that are enabled")
    enabled_start_conditions = models.TextField(default="none", help_text="\\n separated start conditions")
    number_per_condition = models.PositiveIntegerField(default=0, help_text="Number of people per combination of the conditions")
    max_number_of_people = models.PositiveIntegerField(default=0, help_text="Maximum number of people to provision IDs for")
    data_directory = models.CharField(max_length=20, help_text=f"Data directory for user data within '{os.path.join(settings.DROPBOX_ROOT_PATH, settings.DROPBOX_DATA_FOLDER)}'")

    _enabled_study_conditions = _enabled_start_conditions = None

    class Meta:
        verbose_name = _('study management')
        verbose_name_plural = _('study management')

    def __str__(self):
        return f"Max {self.max_number_of_people} people with {self.number_per_condition} per condition"

    @property
    def enabled_start_conditions_list(self):
        if self._enabled_start_conditions is None:
            self._enabled_start_conditions = []
            for condition in self.enabled_start_conditions.split('\n'):
                if condition.strip() in User.StartConditions:
                    self._enabled_start_conditions.append(User.StartConditions(condition.strip()))

        return self._enabled_start_conditions

    @property
    def enabled_study_conditions_list(self):
        if self._enabled_study_conditions is None:
            self._enabled_study_conditions = [x for x in User.StudyConditions if self.check_study_condition(x)]

        return self._enabled_study_conditions

    @property
    def resolved_data_directory(self):
        return os.path.join(settings.DROPBOX_DATA_FOLDER, self.data_directory)

    @staticmethod
    def get_default():
        """Get the default study management object that we shall be using. I
        think this should be a 'manager', but it doesn't really matter now"""
        return StudyManagement.objects.order_by('-pk')[0]

    def check_study_condition(self, condition):
        """Check that the condition, given by an int, is enabled"""
        return (self.enabled_study_conditions & (1 << (condition-1))) > 0

    def check_start_condition(self, condition):
        """Check that the condition, given by a string, is enabled"""
        return condition in self.enabled_start_conditions_list
