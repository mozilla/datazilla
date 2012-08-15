"""
This contains utility functions regarding the stats views.
"""

from datazilla.model import utils



REQUIRE_DAYS_AGO = """Invalid Request: Require days_ago parameter.
                    This specifies the number of days ago to use as the start
                    date range for this response."""

API_CONTENT_TYPE = 'application/json; charset=utf-8'


def get_range(request):
    """Utility function to extract the date range from the request."""

    days_ago = int(request.GET.get("days_ago"))
    numdays = int(request.GET.get("numdays", 0))

    return utils.get_day_range(days_ago, numdays)


