from django.shortcuts import render

# Create your views here.
from django.http import HttpResponseNotFound

def catch_all(request, anything):
    return HttpResponseNotFound(f"Not found: {anything}")