# Models required for data analysis. These should never be populated in prod on
# heroku

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .domain import State, Transition, constants
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
    diagnoses = models.CharField(max_length=60)  # Comma separated list of chosen constants.DIAGNOSES
    diagnosis_certainty = models.IntegerField()
    action = models.CharField(max_length=15, choices=tuple(constants.ACTIONS.items()))
    next_state = models.CharField(max_length=80, null=True, blank=True)

    video_loaded_time = models.DateTimeField()
    video_stop_time = models.DateTimeField()
    dx_selected_time = models.DateTimeField()
    dx_confirmed_time = models.DateTimeField()
    ax_selected_time = models.DateTimeField()

    NOT_CSV_HEADER_FIELDS = ['id', 'user', 'start_timestamp', 'end_timestamp']

    class Meta:
        verbose_name = _('action')
        verbose_name_plural = _('actions')

    def __str__(self):
        return f"{self.user.username}@{self.start_timestamp}"

    @staticmethod
    def csv_headers():
        return []
