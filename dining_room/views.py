from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import User
from .forms import DemographicsForm


# Create your views here.

class DemographicsFormView(LoginRequiredMixin, FormView):
    """
    Display the demographics questionnaire form, validate it, and update the
    User object accordingly
    """
    template_name = 'dining_room/demographics.html'
    form_class = DemographicsForm
    success_url = reverse_lazy('dining_room:instructions')

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
        print(self.get_success_url())
        return super().form_valid(form)


@login_required
def instructions(request):
    return JsonResponse({"instructions": True})
