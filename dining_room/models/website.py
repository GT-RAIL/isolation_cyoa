import csv
import dropbox

from django.db import models
from django.contrib import auth
from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin, BaseUserManager)
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.utils import timezone
from django.utils.crypto import get_random_string, salted_hmac
from django.utils.translation import gettext_lazy as _

from .domain import State, Transition

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

    def create_user(self, username, unique_key, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, unique_key, password, **extra_fields)

    def create_superuser(self, username, unique_key, password, **extra_fields):
        """"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

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

    username = models.CharField(_('username'), max_length=150, unique=True, validators=[username_validator])
    unique_key = models.CharField(_('unique_key'), max_length=150, unique=True)

    # Permissions, etc.
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True) # Used in default User
    date_modified = models.DateTimeField(_('date modified'), auto_now=True)

    # Study condition tracking
    class StudyConditions(models.IntegerChoices):
        """The study conditions"""
        BASELINE = 0, _('Baseline')
        __empty__ = _('(Unknown)')

    study_condition = models.IntegerField(_('study condition'), blank=True, null=True, choices=StudyConditions.choices)

    class StartConditions(models.TextChoices):
        """
        The start conditions. Given by the state description in domain.State
        """
        AT_KC_ABOVE_MUG = 'kc.kc.default.above_mug.default.empty.dt'
        AT_COUNTER_OCCLUDING = 'kc.kc.occluding.default.default.empty.dt'
        AT_COUNTER_OCCLUDING_ABOVE_MUG = 'kc.kc.occluding.above_mug.default.empty.dt'
        AT_COUNTER_MISLOCALIZED = 'dt.kc.default.default.default.empty.kc'  # Remains
        AT_TABLE = 'kc.dt.default.default.default.empty.dt'                 # Remains
        AT_TABLE_ABOVE_MUG = 'kc.dt.default.above_mug.default.empty.dt'     # Remains
        AT_TABLE_OCCLUDING = 'kc.dt.occluding.default.default.empty.dt'     # Remains
        AT_TABLE_OCCLUDING_ABOVE_MUG = 'kc.dt.occluding.above_mug.default.empty.dt' # Remains

        __empty__ = _('(Unknown)')

    start_condition = models.CharField(_('start condition'), max_length=80, blank=True, null=True, choices=StartConditions.choices)
    scenario_completed = models.BooleanField(_('scenario completed?'), blank=True, null=True, default=None)
    date_started = models.DateTimeField(_('date started'), blank=True, null=True)
    date_finished = models.DateTimeField(_('date finished'), blank=True, null=True)  # Not necessarily completed the scenario

    # Demographics. TODO: Do we want region, occupation, etc?
    class AgeGroups(models.IntegerChoices):
        BELOW_20  = 0
        BTW_20_25 = 1
        BTW_25_30 = 2
        BTW_30_35 = 3
        BTW_35_40 = 4
        BTW_40_45 = 5
        BTW_45_50 = 6
        ABOVE_50  = 7

    class ExperienceGroups(models.IntegerChoices):
        NONE = 0
        RARELY = 1
        OCCASIONALLY = 2
        FREQUENTLY = 3
        ALWAYS = 4

    class Genders(models.TextChoices):
        PREFER_NOT_TO_SAY = 'U'  # Unknown
        FEMALE = 'F'
        MALE = 'M'

    age_group = models.IntegerField(choices=AgeGroups.choices, blank=True, null=True)
    robotics_experience = models.IntegerField(choices=ExperienceGroups.choices, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Genders.choices, blank=True, null=True)
    date_demographics_completed = models.DateTimeField(_('date demographics completed'), blank=True, null=True)

    # Likert Responses
    class LikertResponses(models.IntegerChoices):
        STRONGLY_DISAGREE = 0
        DISAGREE = 1
        NEUTRAL = 2
        AGREE = 3
        STRONGLY_AGREE = 4

    long_time_to_recover = models.IntegerField(
        _("It took me a long time to help the robot recover"),
        blank=True, null=True, choices=LikertResponses.choices
    )
    easy_to_diagnose = models.IntegerField(
        _("It was easy to diagnose the error"),
        blank=True, null=True, choices=LikertResponses.choices
    )
    long_time_to_understand = models.IntegerField(
        _("It took me a long time to understand what was wrong with the robot"),
        blank=True, null=True, choices=LikertResponses.choices
    )
    system_helped_resume = models.IntegerField(
        _("The system helped me in assisting the robot"),
        blank=True, null=True, choices=LikertResponses.choices
    )
    easy_to_recover = models.IntegerField(
        _("It was easy to recover from the errors in the task"),
        blank=True, null=True, choices=LikertResponses.choices
    )
    system_helped_understand = models.IntegerField(
        _("The system helped me understand what went wrong with the robot"),
        blank=True, null=True, choices=LikertResponses.choices
    )
    comments = models.TextField(_("Comments and Feedback")) # TODO: Design this generic feedback
    date_survey_completed = models.DateTimeField(_('date survey completed'), blank=True, null=True)

    # TODO: Add REACTION questionnaire questions? Or perhaps from Knepper

    # TODO: Add gold standard questions

    # Required constants
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'unique_key'  # Just in case some code actually uses it
    REQUIRED_FIELDS = ['unique_key']

    # Associate the manager and the meta information
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @property
    def csv_file(self):
        """The CSV file associated with the user's actions"""
        return f"{self.username.lower()}.csv"


# class Demographics(models.Model):
#     """
#     An unmanaged model to provide a view into the demographics information of
#     the user. The information here is just to show the data in the admin UI
#     """
#     # TODO

#     class Meta:
#         db_table = 'dining_room_user'
#         managed = False
