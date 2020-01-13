from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def demographics(request):
    return JsonResponse({"demographics": True})

@login_required
def instructions(request):
    return JsonResponse({"instructions": True})
