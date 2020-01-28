from django import forms
from django.forms import ModelForm
from django.utils import timezone

from .models import User


# Create the forms here

class DemographicsForm(ModelForm):
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


class InstructionsTestForm(ModelForm):
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
                raise forms.ValidationError("One of the questions has been incorrectly answered")

        return cleaned_data


class SurveyForm(ModelForm):
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
