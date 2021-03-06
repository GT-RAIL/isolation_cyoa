# Models required for data analysis. These should never be populated in prod on
# heroku

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import multiselectfield

from .. import constants
from .domain import State, Transition, Suggestions
from .website import User, StudyManagement


# Model for the action streams

class StudyAction(models.Model):
    """
    A model for the data that we're saving in CSV form in production. We
    translate the data there into a database model that we can then use for
    data processing however we wish to.

    This should never be populated with the `dropbox_to_db` and `db_to_dropbox`
    scripts. Instead, prefer the use of another script that converts CSV data
    into rows amenable to this model
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_timestamp = models.DateTimeField()     # This is the timestamp one row above in the CSV
    end_timestamp = models.DateTimeField()       # This is the timestamp on the same row

    start_state = models.CharField(max_length=80)
    diagnoses = multiselectfield.MultiSelectField(choices=tuple(constants.DIAGNOSES.items()))
    diagnosis_certainty = models.IntegerField()
    action = models.CharField(max_length=20, choices=tuple(constants.ACTIONS.items()))
    next_state = models.CharField(max_length=80, null=True, blank=True)

    video_loaded_time = models.DateTimeField()
    video_stop_time = models.DateTimeField()
    dx_selected_time = models.DateTimeField()
    dx_confirmed_time = models.DateTimeField()
    ax_selected_time = models.DateTimeField()

    # Other data not part of the JSON action information
    browser_refreshed = models.BooleanField(default=False)
    corrupted_dx_suggestions = models.BooleanField(default=False)
    corrupted_ax_suggestions = models.BooleanField(default=False)
    dx_suggestions = multiselectfield.MultiSelectField(choices=tuple(constants.DIAGNOSES.items()), blank=True, null=True)
    ax_suggestions = multiselectfield.MultiSelectField(choices=tuple(constants.ACTIONS.items()), blank=True, null=True)

    # Cached property
    _action_idx = None

    # Fields that should not be part of the JSON action information
    NOT_CSV_HEADER_FIELDS = [
        'id',
        'user',
        'start_timestamp',
        'end_timestamp',
        'browser_refreshed',
        'dx_suggestions',
        'ax_suggestions',
        # The corrupted flags should be populated post-processing, but they
        # are now forever part of the CSV header
    ]

    class Meta:
        verbose_name = _('study action')
        verbose_name_plural = _('study actions')

    def __str__(self):
        return f"{self.user.username}, {self.action_idx}"

    @staticmethod
    def get_csv_headers():
        """
        Headers corresponding to the fields that should be present in the CSV.
        The returned value is used by the `utils` code to figure out how to
        structure the CSV
        """
        return [x.name for x in StudyAction._meta.get_fields() if x.name not in StudyAction.NOT_CSV_HEADER_FIELDS]

    @property
    def action_idx(self):
        """Get the action index for the given user"""
        if self._action_idx is None:
            self._action_idx = StudyAction.objects.filter(user=self.user, start_timestamp__lt=self.start_timestamp).count()

        return self._action_idx

    @property
    def duration(self):
        return (self.end_timestamp - self.start_timestamp) if self.start_timestamp is not None else None

    @property
    def dx_decision_duration(self):
        return (self.dx_selected_time - self.video_stop_time) if self.video_stop_time is not None else None

    @property
    def ax_decision_duration(self):
        return (self.ax_selected_time - self.dx_confirmed_time) if self.dx_confirmed_time is not None else None

    @property
    def decision_duration(self):
        return (self.ax_selected_time - self.video_stop_time) if self.video_stop_time is not None else None

    @property
    def chose_dx_suggestion(self):
        if self.diagnoses is None or self.dx_suggestions is None:
            return None
        return len(set(self.diagnoses) & set(self.dx_suggestions)) > 0

    @property
    def chose_ax_suggestion(self):
        # None of the data will hit this. So instead we return 0 (not NA) when
        # there are no AX suggestions
        if self.action is None or self.ax_suggestions is None:
            return None
        return self.action in self.ax_suggestions

    @property
    def chose_dx_optimal(self):
        if self.start_state is None or self.diagnoses is None:
            return None
        state = State(eval(self.start_state))
        optimal_dx = Suggestions().ordered_diagnoses(state, None, accumulate=True)
        return len(set(self.diagnoses) & set(optimal_dx)) > 0

    @property
    def chose_ax_optimal(self):
        if self.start_state is None or self.action is None:
            return None
        state = State(eval(self.start_state))
        optimal_ax = Suggestions().optimal_action(state, None)
        return self.action in optimal_ax
