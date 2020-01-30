import datetime
import logging

from django import forms
from django.db.models import Q
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

    DATE_JOINED_TIMEDELTA = datetime.timedelta(minutes=20)

    def __init__(self, request=None, *args, **kwargs):
        """Initialize the same way as an AuthenticationForm"""
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

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

    def clean(self):
        cleaned_data = super().clean()

        # Check to see if there are conditions that need to be satisfied on the
        # manager and create a user if so
        sm = StudyManagement.get_default()

        # First check that we haven't exceeded the max number of users
        users_not_staff = Q(is_staff=False)
        users_valid_condition = Q(ignore_data_reason__isnull=True)
        # date_joined_condition = Q(date_joined__gte=(timezone.now()-CreateUserForm.DATE_JOINED_TIMEDELTA))
        # date_finished_condition = Q(date_finished__isnull=False)
        number_of_users = User.objects.filter(users_not_staff & users_valid_condition).count()
        if sm.max_number_of_people <= number_of_users:
            raise forms.ValidationError("Cannot create user")

        # Then iterate through the conditions and create a user. We can optimize
        # this to start with the minimum number of users in a given condition.
        user = None
        for num_users in range(1, sm.number_per_condition+1):
            for study_condition in sm.enabled_study_conditions_list:
                for start_condition in sm.enabled_start_conditions_list:
                    # Check the number of active users, if less add a user, else
                    # continue
                    users_in_condition = Q(start_condition=start_condition, study_condition=study_condition)
                    number_users_in_condition = User.objects.filter(
                        users_in_condition
                        & users_not_staff
                        & users_valid_condition
                        # & (date_joined_condition | date_finished_condition)
                    ).count()
                    if number_users_in_condition < num_users:
                        user = self._create_user(study_condition, start_condition)
                        logger.info(f"{user} created for {start_condition}, {study_condition}")
                        break

                # Exit if we've created an user
                if user is not None:
                    break

            # Exit if we've created an user
            if user is not None:
                break

        # Raise an error if we didn't manage to create a user
        if user is None:
            raise forms.ValidationError("Cannot create user")

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

        # Get workers with the same ID
        num_failed_workers = User.objects.filter(amt_worker_id=cleaned_data['amt_worker_id'], ignore_data_reason__isnull=False).count()
        if num_failed_workers > 0:
            self.instance.ignore_data_reason = f"failed worker ID of {cleaned_data['amt_worker_id']} is repeated"
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
            raise forms.ValidationError(errors)

        # Then check to see the knowledge review answers, and update the
        # instance if the review is incorrect
        for key in self.fields:
            if cleaned_data.get(key, 'Unknown') != self.acceptable_answers[key]:
                self.instance.number_incorrect_knowledge_reviews += 1
                self.instance.save()

                # Check to see if this user must be booted out of the system
                if self.instance.number_incorrect_knowledge_reviews < self.instance.study_management.max_test_attempts:
                    raise forms.ValidationError("At least one of your answers is incorrect")
                else:
                    self.instance.ignore_data_reason = f"failed knowledge review {self.instance.number_incorrect_knowledge_reviews} times"
                    self.instance.save()

        return cleaned_data


class SurveyForm(forms.ModelForm):
    """
    The model form for taking the survey at the end of the experiment
    """

    class Meta:
        model = User
        fields = [
            'certain_of_actions',
            'not_sure_how_to_help',
            'system_helped_understand',
            'could_not_identify_problems',
            'information_was_enough',
            'identify_problems_in_future',
            'system_was_responsible',
            'rely_on_system_in_future',
            'user_was_competent',
            'comments',
        ]

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
