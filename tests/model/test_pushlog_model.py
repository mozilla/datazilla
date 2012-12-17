import json
import datetime
import copy
import urllib

from ..sample_pushlog import get_pushlog_json_set, get_pushlog_json_readable


def get_branch_id(plm):
    """Use the Firefox branch as our common test branch"""
    branch = plm.get_branch_list("Firefox")
    return branch[0]["id"]

def get_alt_name_branch_id(plm):
    """Use the Firefox-Non-PGO branch to retrieve id"""
    branch = plm.get_branch_list("Firefox-Non-PGO")
    return branch[0]["id"]


def test_branches(plm):
    """
    Test get_branch_list to return all branches.

    Opted to not check each value and specific count in case we change the
    number of branches in the future.
    """
    branches = plm.get_branch_list()

    assert len(branches) > 0


def test_single_branch(plm):
    """Test get_branch_list with a branch that exists."""
    branches = plm.get_branch_list("Firefox")

    assert len(branches) == 1

def test_single_alt_name_branch(plm):
    """Test get_branch_list with an alt_name branch that exists."""
    branches = plm.get_branch_list("Firefox-Non-PGO")

    assert len(branches) == 1


def test_single_branch_not_found(plm):
    """Test the get_branch_list method with non-existent branch."""
    branches = plm.get_branch_list("Cortexiphan")

    assert not branches


def test_get_params(plm):
    """Test the get_params method."""
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


def test_get_all_changesets(plm):
    """Ensure that get_all_changesets returns all the changesets from all pushes"""
    branch_id = get_branch_id(plm)
    data = json.loads(get_pushlog_json_set())
    plm._insert_branch_pushlogs(branch_id, data)

    #verify that the data that was inserted matches the JSON source data.
    changesets = plm.get_all_changesets()
    exp_changesets = []
    for pl in data.values():
        exp_changesets.extend(pl["changesets"])

    assert len(exp_changesets) == len(changesets)
    for cs in changesets:
        exp_cs = [x for x in exp_changesets if x["node"] == str(cs["node"])][0]
        for key in ["node", "author", "branch", "desc"]:
            assert str(exp_cs[key]) == str(cs[key])



def test_insert_branch_pushlogs_happy_path(plm):
    """
    Test insert_branch_pushlogs.

    Verify counts on return status as well as all the data inserted into the
    db.

    """
    branch_id = get_branch_id(plm)
    data = json.loads(get_pushlog_json_set())
    plm._insert_branch_pushlogs(branch_id, data)

    # branch count is incremented in store_pushlogs, not here, so exp 0
    assert plm.branch_count == 0

    assert plm.pushlog_count == 3
    assert plm.changeset_count == 7
    assert plm.pushlog_skipped_count == 0
    assert plm.changeset_skipped_count == 0

    #verify that the data that was inserted matches the JSON source data.
    pushlogs = plm.get_all_pushlogs()
    assert len(pushlogs) == len(data)

    for pl in pushlogs:
        exp_pl = data[str(pl["push_id"])]
        for key in ["date", "user"]:
            assert str(exp_pl[key]) == str(pl[key])
        assert str(branch_id) == str(pl["branch_id"])

        exp_changesets = exp_pl["changesets"]

        changesets = plm.get_changesets(pushlog_id=pl["id"])
        assert len(exp_changesets) == len(changesets)
        for cs in changesets:
            exp_cs = [x for x in exp_changesets if x["node"] == str(cs["node"])][0]
            for key in ["node", "author", "branch", "desc"]:
                assert str(exp_cs[key]) == str(cs[key])
            assert pl["id"] == cs["pushlog_id"]


def test_insert_branch_pushlogs_twice_skips(plm):
    """Trying to insert the same pushlog twice causes them to be skipped"""
    branch_id = get_branch_id(plm)
    data = json.loads(get_pushlog_json_set())
    plm._insert_branch_pushlogs(branch_id, data)

    assert plm.pushlog_count == 3

    plm.reset_counts()
    plm._insert_branch_pushlogs(branch_id, data)

    assert plm.branch_count == 0
    assert plm.pushlog_count == 0
    assert plm.changeset_count == 0
    assert plm.pushlog_skipped_count == 3
    assert plm.changeset_skipped_count == 7


def test_insert_branch_pushlogs_dup_changeset(plm):
    """
    Trying to insert a pushlog with a duplicate changeset causes just
    the changeset to be skipped

    """

    branch_id = get_branch_id(plm)
    data = json.loads(get_pushlog_json_set())
    cs = data["23046"]["changesets"][0]
    dup = copy.deepcopy(cs)
    data["23046"]["changesets"].append(dup)

    plm._insert_branch_pushlogs(branch_id, data)

    assert plm.branch_count == 0
    assert plm.pushlog_count == 3
    assert plm.changeset_count == 7
    assert plm.pushlog_skipped_count == 0
    assert plm.changeset_skipped_count == 1


def test_store_pushlogs_happy_path(plm, monkeypatch):
    """
    Test store pushlog method.

    monkeypatch urllib to return our canned data.

    """
    def mock_urlopen(nuttin_honey):
        return get_pushlog_json_readable(get_pushlog_json_set())
    monkeypatch.setattr(urllib, 'urlopen', mock_urlopen)

    result = plm.store_pushlogs("test_host", 1, branch="Firefox")

    exp_result = {
        "branches": 1,
        "pushlogs_stored": 3,
        "changesets_stored": 7,
        "pushlogs_skipped": 0,
        "changesets_skipped": 0,
        }

    assert result == exp_result


def test_store_pushlogs_no_data(plm, monkeypatch):
    """
    Test store pushlog method when no json is returned for the specified branch.

    monkeypatch urllib to return our canned data.

    """
    def mock_urlopen(nuttin_honey):
        return get_pushlog_json_readable("")
    monkeypatch.setattr(urllib, 'urlopen', mock_urlopen)

    result = plm.store_pushlogs("test_host", 1, branch="Firefox")

    exp_result = {
        "branches": 0,
        "pushlogs_stored": 0,
        "changesets_stored": 0,
        "pushlogs_skipped": 0,
        "changesets_skipped": 0,
        }

    assert result == exp_result

def test_get_branch_pushlog(plm, monkeypatch):

    data = json.loads(get_pushlog_json_set())

    def mock_urlopen(nuttin_honey):
        return get_pushlog_json_readable(get_pushlog_json_set())
    monkeypatch.setattr(urllib, 'urlopen', mock_urlopen)

    result = plm.store_pushlogs("test_host", 1, branch="Firefox")

    branch_pushlog = plm.get_branch_pushlog(1)

    data_nodes = set()
    branch_nodes = set()

    #Get nodes for sample data
    for push_id in data:
        for node in data[push_id]['changesets']:
            data_nodes.add(node['node'])

    #Get all branch nodes retrieved
    for push_data in branch_pushlog:
        branch_nodes.add( push_data['node'] )

    #sample data nodes should match branch nodes retrieved
    assert data_nodes == branch_nodes

