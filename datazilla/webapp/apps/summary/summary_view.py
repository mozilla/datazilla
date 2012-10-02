import datetime
import json
import urllib
import zlib

from django.shortcuts import render_to_response
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


def summary_page(request, project="", branch="", revision=""):

    return render_to_response('metrics.summary.html', {})

