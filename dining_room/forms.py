import datetime
import logging
import itertools

from django import forms
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login
from django.utils import timezone

from .models import User, StudyManagement


# Create the forms here

logger = logging.getLogger(__name__)


class CreateUserForm(forms.Form):
    """
    A form to create a user (if the study conditions allow for it), and log them
    in if successful. If not, a validation error is raised. The form takes
    nothing as input
    """

    ALLOWED_TIME_SINCE_LOGIN = datetime.timedelta(minutes=46)

    def __init__(self, request=None, *args, **kwargs):
        """Initialize the same way as an AuthenticationForm"""
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Cache a pointer to the study manager
        self._sm = None
        self._conditions_idx = None
        self._conditions_aggregate = None

    def _create_user(self, study_condition, start_condition):
        # Loop through to make sure that we never have duplicates
        username = unique_key = None
        while ((username is None or unique_key is None)):
            username_candidate = User.objects.make_random_password(allowed_chars='abcdefghjkmnpqrstuvwxyz23456789')
            unique_key_candidate = User.objects.make_random_password(allowed_chars='abcdefghjkmnpqrstuvwxyz23456789')
            num_existing_users = User.objects.filter(Q(username=username_candidate) | Q(unique_key=unique_key_candidate)).count()
            if num_existing_users == 0:
                username, unique_key = username_candidate, unique_key_candidate

        # Create the user
        user = User.objects.create_user(username, unique_key, study_condition=study_condition, start_condition=start_condition)
        return user

    def _clear_abandoned_users(self):
        """
        Clear out users that might've abandoned the study
        """
        User.objects.filter(
            Q(date_survey_completed__isnull=True) &
            (Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason='')) &
            Q(last_login__lte=(timezone.now() - CreateUserForm.ALLOWED_TIME_SINCE_LOGIN))
        ).update(
            ignore_data_reason = f'marked as abandoned at {timezone.now()}'
        )

    def _get_study_management(self):
        """Get a study manager. We cache the expensive aggregate generator"""
        sm = StudyManagement.get_default()
        if sm != self._sm:
            self._sm = sm
            self._conditions_idx = {}
            self._conditions_aggregate = {}
            for idx, (study_condition, start_condition) in enumerate(itertools.product(sm.enabled_study_conditions_list, sm.enabled_start_conditions_list)):
                self._conditions_aggregate[str(idx)] = Count('pk', filter=Q(study_condition=study_condition, start_condition=start_condition))
                self._conditions_idx[str(idx)] = (study_condition, start_condition)
        return sm

    def clean(self):
        cleaned_data = super().clean()
        self._clear_abandoned_users()

        # Get the management object
        sm = self._get_study_management()

        # Create the different filter conditions and make a queryset from that
        users_not_staff = Q(is_staff=False)
        users_valid_condition = Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason='')
        users_enabled_conditions = (Q(study_condition__in=sm.enabled_study_conditions_list) & Q(start_condition__in=sm.enabled_start_conditions_list))
        qs = User.objects.filter(users_not_staff & users_valid_condition & users_enabled_conditions)

        # First check that we haven't exceeded the max number of users
        number_of_users = qs.count()
        if sm.max_number_of_people <= number_of_users:
            raise forms.ValidationError("Exceeded max number; cannot create user")

        # Get the number of users per condition
        counts_per_condition = qs.aggregate(**self._conditions_aggregate)
        min_count = float('inf')
        assigned_condition = None
        for cidx, count in counts_per_condition.items():
            if count > min_count or count >= sm.number_per_condition:
                continue

            min_count = count
            assigned_condition = self._conditions_idx[cidx]

        # If a condition exists, then pick the user, otherwise return a fail
        if assigned_condition is None:
            raise forms.ValidationError("Exceeded number per condition; cannot create user")

        user = self._create_user(*assigned_condition)
        logger.info(f"{user} created for {assigned_condition[0]}, {assigned_condition[1]}")

        # Authenticate the user in
        self.user_cache = authenticate(self.request, username=user.username, password=user.username)
        if self.user_cache is None:
            raise forms.ValidationError("Cannot authenticate user")

        # Log the user in
        self.user_cache = login(self.request, self.user_cache)

        # Return the cleaned data
        return cleaned_data


class DemographicsForm(forms.ModelForm):
    """
    The model form related to the demographics questionnaire
    """

    class Meta:
        model = User
        fields = ['amt_worker_id', 'age_group', 'gender', 'robot_experience']

    def __init__(self, *args, **kwargs):
        # Initialize the form
        super().__init__(*args, **kwargs)

        # Make these fields required
        for key in self.fields:
            self.fields[key].required = True

    def clean(self):
        """Check to see if a known failed AMT worker has tried this again"""
        cleaned_data = super().clean()
        if not cleaned_data.get('amt_worker_id'):
            raise forms.ValidationError("Worker ID needs to be filled in.")

        # Get workers with the same ID
        num_repeated = User.objects.filter(amt_worker_id=cleaned_data['amt_worker_id']).count()
        if num_repeated > 0:
            self.instance.ignore_data_reason = f"worker ID of {cleaned_data['amt_worker_id']} is repeated"
            self.instance.save()

    def save(self, *args, **kwargs):
        """Update the date that demographics information was completed"""
        self.instance.date_demographics_completed = timezone.now()
        return super().save(*args, **kwargs)


class InstructionsTestForm(forms.ModelForm):
    """
    The model form related to the demographics questionnaire. We do minimal
    checking on this data and simply proceed
    """

    class Meta:
        model = User
        fields = [x[0] for x in User.ACCEPTABLE_REVIEW_ANSWERS]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the answers as a dict
        self.acceptable_answers = dict(User.ACCEPTABLE_REVIEW_ANSWERS)

    def clean(self):
        """Customize the cleaning of this form to disallow empty responses or
        incorrect responses"""
        cleaned_data = super().clean()

        # First check to see if any questions are blank. Force an answer of all
        # questions so that people cannot game the system
        errors = []
        for key in self.fields:
            if cleaned_data.get(key) is None:
                errors.append(forms.ValidationError("The question '%(question)s' must be answered", params={'question': self.fields[key].label}))

        if len(errors) > 0:
            self.instance.number_incorrect_knowledge_reviews += 1
            self.instance.save()

            # Only surface the error if the user should not be booted out
            if self.instance.number_incorrect_knowledge_reviews < self.instance.study_management.max_test_attempts:
                raise forms.ValidationError(errors)

        # Then check to see the knowledge review answers, and update the
        # instance if the review is incorrect
        else:
            for key in self.fields:
                if cleaned_data.get(key, 'Unknown') != self.acceptable_answers[key]:
                    self.instance.number_incorrect_knowledge_reviews += 1
                    self.instance.save()

                    # Only surface the error if the user should not be booted out
                    if self.instance.number_incorrect_knowledge_reviews < self.instance.study_management.max_test_attempts:
                        raise forms.ValidationError("At least one of your answers is incorrect")

        # Check to see if we must fail this user out of the study
        if self.instance.number_incorrect_knowledge_reviews >= self.instance.study_management.max_test_attempts:
            self.instance.ignore_data_reason = f"failed knowledge review {self.instance.number_incorrect_knowledge_reviews} times"
            self.instance.save()

        return cleaned_data


class SurveyForm(forms.ModelForm):
    """
    The model form for taking the survey at the end of the experiment
    """

    class Meta:
        model = User
        fields = (
            User.CUSTOM_SURVEY_FIELD_NAMES +
            User.SUS_SURVEY_FIELD_NAMES +
            ['comments']
        )

    def __init__(self, *args, **kwargs):
        # Initialize the form
        super().__init__(*args, **kwargs)

        # Make all fields barring the comments required (but update CSS classes)
        # on the comments
        for key in self.fields:
            if key == 'comments':
                self.fields[key].widget.attrs.update({
                    'class': 'form-control',
                    'rows': 10,
                    'cols': "100%"
                })
                continue

            self.fields[key].required = True

    def save(self, *args, **kwargs):
        """Update the date the survey was completed"""
        self.instance.date_survey_completed = timezone.now()
        return super().save(*args, **kwargs)
