import json
import datetime
import copy

from datazilla.model.base import TestDataError, TestData

from ..sample_pushlog import pushlog_json



def test_unicode(plm):
    """Unicode representation of a ``DatazillaModel`` is the project name."""
    assert unicode(plm) == u"testpushlog"


def test_branches(plm):
    branches = plm.get_branch_list()

    assert len(branches) > 0


def test_single_branch(plm):
    branches = plm.get_branch_list("Firefox")

    assert len(branches) == 1


def test_single_branch_not_found(plm):
    branches = plm.get_branch_list("Cortexiphan")

    assert branches == None


def test_get_params(plm):
    params = plm.get_params(4, enddate="06/10/2012")

    exp_params = {
        "startdate": "06/06/2012",
        "enddate": "06/10/2012",
        "full": 1,
        }
    assert params == exp_params


def test_get_params_no_enddate(plm):
    """
    datetime.date.today is immutable, so monkeypatch doesn't work.

    """
    class TodayDate(datetime.date):
        @classmethod
        def today(cls):
            return datetime.date(month=6, day=10, year=2012)

    originaldate = datetime.date
    datetime.date = TodayDate

    params = plm.get_params(4)

    exp_params = {
        "startdate": "06/06/2012",
        "full": 1,
        }

    assert params == exp_params

    # set date back how it was.  is this necessary?
    datetime.date = originaldate


def test_insert_branch_pushlogs(plm):
    data = json.loads(pushlog_json())
    plm._insert_branch_pushlogs(1, data)

    # branch count is incremented in store_pushlogs, not here, so exp 0
    assert plm.branch_count == 0

    assert plm.pushlog_count == 3
    assert plm.changeset_count == 7
    assert plm.pushlog_skipped_count == 0
    assert plm.changeset_skipped_count == 0


def test_insert_branch_pushlogs_twice_skips(plm):
    """Trying to insert the same pushlog twice causes them to be skipped"""
    data = json.loads(pushlog_json())
    plm._insert_branch_pushlogs(1, data)

    assert plm.pushlog_count == 3

    plm.reset_counts()
    plm._insert_branch_pushlogs(1, data)

    assert plm.branch_count == 0
    assert plm.pushlog_count == 0
    assert plm.changeset_count == 0
    assert plm.pushlog_skipped_count == 3
    assert plm.changeset_skipped_count == 7


def xtest_insert_branch_pushlogs_dup_changeset(plm):
    """
    Trying to insert a pushlog with a duplicate changeset causes just
    the changeset to be skipped

    """

    data = json.loads(pushlog_json())
#    cs = data["23046"]["changesets"][0]
#    dup = copy.deepcopy(cs)
#    data["23046"]["changesets"].append(dup)
#
#    print data

    plm._insert_branch_pushlogs(1, data)

    assert plm.branch_count == 0
    assert plm.pushlog_count == 3
    assert plm.changeset_count == 7
    assert plm.pushlog_skipped_count == 0
    assert plm.changeset_skipped_count == 1
