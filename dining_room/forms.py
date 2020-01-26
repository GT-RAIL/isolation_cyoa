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
        fields = [
            'supposed_to_grab_bowl',
            'supposed_to_go_to_couch',
            'will_view_in_first_person',
            'supposed_to_select_only_one_error',
            'actions_involve_invisible_arm_motion',
        ]

    def clean(self):
        """Customize the cleaning of this form to disallow empty responses"""
        cleaned_data = super().clean()

        errors = []
        for key in self.fields:
            if cleaned_data.get(key) is None:
                errors.append(forms.ValidationError("The question '%(question)s' must be answered", params={'question': self.fields[key].label}))

        if len(errors) > 0:
            raise forms.ValidationError(errors)

        return cleaned_data


class SurveyForm(ModelForm):
    """
    The model form for taking the survey at the end of the experiment
    """

    class Meta:
        model = User
        fields = [
            'long_time_to_recover',
            'easy_to_diagnose',
            'long_time_to_understand',
            'system_helped_resume',
            'easy_to_recover',
            'system_helped_understand',
            'comments'
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
