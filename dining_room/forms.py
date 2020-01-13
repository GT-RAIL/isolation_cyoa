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
        fields = ['age_group', 'gender', 'robotics_experience']

    def __init__(self, *args, **kwargs):
        # Initialize the form
        super().__init__(*args, **kwargs)

        # Make these fields required
        for key in self.fields:
            self.fields[key].required = True
