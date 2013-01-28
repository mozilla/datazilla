import datetime
import json
import urllib
import zlib

from django.shortcuts import render_to_response
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


def summary_page(request, project="", branch="", revision=""):

    #give template access to the DEBUG variable
    template_context = { 'DEBUG':settings.DEBUG }

    return render_to_response(
        'metrics.summary.html', template_context
        )

def apps_summary_page(request, project="", branch="", revision=""):

    #give template access to the DEBUG variable
    template_context = { 'DEBUG':settings.DEBUG }

    return render_to_response(
        'apps.summary.html', template_context
        )
