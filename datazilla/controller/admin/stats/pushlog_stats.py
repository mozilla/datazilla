from django.core.exceptions import FieldError

from datazilla.model.stats import PushlogStatsModel, PerformanceTestStatsModel
from datazilla.model import utils

def get_not_referenced(project, startdate, enddate, branches=None):
    """Return a list of test runs by in pushlogs not in Datazilla"""

    branches = branches or get_all_branches()

    ptm = PerformanceTestStatsModel(project)
    tr_set = ptm.get_distinct_test_run_revisions()
    ptm.disconnect()

    plm = PushlogStatsModel()
    result = plm.get_pushlogs_not_in_set_by_branch(
        tr_set,
        startdate,
        enddate,
        branches,
        )

    plm.disconnect()

    return result


def get_all_branches():
    plm = PushlogStatsModel()
    return [x["name"] for x in plm.get_all_branches()]