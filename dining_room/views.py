from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import User
from .forms import DemographicsForm, InstructionsTestForm


# Create your views here.

class AbstractFormView(LoginRequiredMixin, FormView):
    """
    An abstract class for all the forms in our app
    """

    def get_form_kwargs(self):
        """Override the instance using the request"""
        kwargs = super().get_form_kwargs()

        # If this object has been saved before, fetch that, else get the user
        # from the request
        if hasattr(self, 'object'):
            kwargs['instance'] = self.object
        else:
            assert hasattr(self.request, 'user') and self.request.user.is_authenticated, \
                f"The request ({self.request}) does not have an authenticated user"
            kwargs['instance'] = self.request.user

        return kwargs

    def form_valid(self, form):
        """
        The form is valid, save the instance
        """
        self.object = form.save()
        return super().form_valid(form)


class DemographicsFormView(AbstractFormView):
    """
    Display the demographics questionnaire form, validate it, and update the
    User object accordingly
    """
    template_name = 'dining_room/demographics.html'
    form_class = DemographicsForm
    success_url = reverse_lazy('dining_room:instructions')


class InstructionsTestView(AbstractFormView):
    """
    Display the gold standard questions for the instructions and save the data
    """
    template_name = 'dining_room/instructions_test.html'
    form_class = InstructionsTestForm
    success_url = reverse_lazy('dining_room:study')


@login_required
def instructions(request):
    return render(request, 'dining_room/instructions.html')


@login_required
def study_template(request):
    return JsonResponse({'videos': True})
