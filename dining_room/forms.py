import datetime
import logging

from django import forms
from django.db.models import Q
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

    def _create_user(self, study_condition, start_condition):
        username = User.objects.make_random_password(allowed_chars='abcdefghjkmnpqrstuvwxyz23456789')
        unique_key = User.objects.make_random_password(allowed_chars='abcdefghjkmnpqrstuvwxyz23456789')
        user = User.objects.create_user(username, unique_key, study_condition=study_condition, start_condition=start_condition)
        return user

    def clean(self):
        cleaned_data = super().clean()

        # Check to see if there are conditions that need to be satisfied on the
        # manager and create a user if so
        sm = StudyManagement.get_default()

        # First check that we haven't exceeded the max number of users
        number_of_users = User.objects.filter(is_staff=False).count()
        if sm.max_number_of_people <= number_of_users:
            raise forms.ValidationError("Cannot create form")

        # Then iterate through the conditions and create a user. We can optimize
        # this to start with the minimum number of users in a given condition.
        user = None
        for num_users in range(1, sm.number_per_condition+1):
            for study_condition in sm.enabled_study_conditions_list:
                for start_condition in sm.enabled_start_conditions_list:
                    users_in_condition = Q(is_staff=False, start_condition=start_condition, study_condition=study_condition)
                    # date_joined_condition = Q(date_joined__gte=(timezone.now()-CreateUserForm.DATE_JOINED_TIMEDELTA))
                    # date_finished_condition = Q(date_finished__isnull=False)

                    # Check the number of active users, if less add a user, else
                    # continue
                    number_users_in_condition = User.objects.filter(
                        users_in_condition
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
            raise forms.ValidationError("Cannot create form")

        # Return the cleaned data
        return cleaned_data


class DemographicsForm(forms.ModelForm):
    """
    The model form related to the demographics questionnaire
    """

    class Meta:
        model = User
        fields = ['age_group', 'gender', 'robot_experience']

    def __init__(self, *args, **kwargs):
        # Initialize the form
        super().__init__(*args, **kwargs)

        # Make these fields required
        for key in self.fields:
            self.fields[key].required = True

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
            raise forms.ValidationError(errors)

        # Then check to see the knowledge review answers, and update the
        # instance if the review is incorrect
        for key in self.fields:
            if cleaned_data.get(key, 'Unknown') != self.acceptable_answers[key]:
                self.instance.number_incorrect_knowledge_reviews += 1
                self.instance.save()
                raise forms.ValidationError("Atleast one of your answers is incorrect")

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
