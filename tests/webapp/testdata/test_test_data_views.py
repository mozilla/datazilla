import json

from datazilla.controller.admin.refdata import perftest_refdata
from tests.sample_data import create_date_based_data, perftest_data
from tests.sample_metric_data import get_metric_values
from datazilla.model import utils, factory
from tests.model.test_metrics_test_model import setup_pushlog_walk_tests

from datazilla.controller.admin.testdata import get_metrics_pushlog

from datazilla.model.base import TestData

def test_get_test_data(client, ptm):
    """
    Test raw test data retrieval through the web service
    """

    sample_data = TestData(perftest_data())
    revision = sample_data['test_build']['revision']
    branch = sample_data['test_build']['branch']

    uri = "/{0}/testdata/raw/{1}/{2}".format(ptm.project, branch, revision)

    #Store and process object
    ptm.store_test_data( json.dumps( sample_data ) )
    ptm.process_objects(1)

    response = client.get(uri)

    assert response.json[0] == sample_data

def test_get_test_data_parameters(client, ptm):
    """
    Test raw test data retrieval with all available query parameters.
    """

    sample_data = TestData(perftest_data())
    revision = sample_data['test_build']['revision']
    branch = sample_data['test_build']['branch']

    uri = "/{0}/testdata/raw/{1}/{2}".format(ptm.project, branch, revision)

    #Store and process object
    ptm.store_test_data( json.dumps( sample_data ) )
    ptm.process_objects(1)

    parameters = _get_uri_parameters(sample_data)

    for params in parameters:

        uri_with_params = "{0}?{1}".format(
            uri, params['query_params']
            )
        fail_uri_with_params = "{0}?{1}".format(
            uri, params['fail_params']
            )

        success_response = client.get(uri_with_params)
        fail_response = client.get(fail_uri_with_params)

        if 'page_name' in params['query_params']:

            #page name filter will only return the pages that match
            #the page name specified.  Build a sample data structure
            #that matches.
            page_sample = sample_data.copy()
            page_filter = sample_data['results']['three.com']
            page_sample['results'] = { 'three.com':page_filter }

            assert success_response.json[0] == page_sample

            #Failed page result will return the rest of the
            #data associated with the test but results will be
            #empty
            assert fail_response.json[0]['results'] == {}

        else:
            assert success_response.json[0] == sample_data
            assert fail_response.json == []

def test_get_metrics_data(client, mtm, ptm, plm, monkeypatch):
    """
    Test metrics data retrieval through the web service.
    """

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch, True)

    metric_values = get_metric_values()

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    for index, revision in enumerate(setup_data['sample_revisions']):

        uri = "/{0}/testdata/metrics/{1}/{2}".format(
            ptm.project, setup_data['branch'], revision
            )

        response = client.get(uri)

        if revision == fail_revision:
            #All tests should fail
            for page in response.json[0]['pages']:

                metric_struct = response.json[0]

                h0_rejected = metric_struct['pages'][page]['h0_rejected']
                fdr = metric_struct['pages'][page]['fdr']
                teval = metric_struct['pages'][page]['test_evaluation']

                assert h0_rejected == 1
                assert fdr == 1
                assert teval == 0

        elif revision == skip_revision:

            assert response.json == []

        else:
            #All tests should pass
            if index > 0:

                for page in response.json[0]['pages']:

                    metric_struct = response.json[0]

                    h0_rejected = metric_struct['pages'][page]['h0_rejected']
                    fdr = metric_struct['pages'][page]['fdr']
                    teval = metric_struct['pages'][page]['test_evaluation']

                    assert h0_rejected == 0
                    assert fdr == 0
                    assert teval == 1

                    revision_metric_values = \
                        set(metric_struct['pages'][page].keys())

                    assert metric_values.issubset(revision_metric_values)

def test_get_metrics_data_with_parameters(
    client, mtm, ptm, plm, monkeypatch
    ):
    """
    Test metrics data retrieval with all available query parameters.
    """

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch, True)

    metric_values = get_metric_values()

    sample_data = TestData(perftest_data())

    sample_data['test_build']['branch'] = setup_data['branch']
    parameters = _get_uri_parameters(sample_data)

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    revision = setup_data['sample_revisions'][3]

    uri = "/{0}/testdata/metrics/{1}/{2}".format(
        ptm.project, setup_data['branch'], revision
        )

    reference_response = client.get(uri)

    for params in parameters:

        uri_with_params = "{0}?{1}".format(
            uri, params['query_params']
            )
        fail_uri_with_params = "{0}?{1}".format(
            uri, params['fail_params']
            )

        success_response = client.get(uri_with_params)
        fail_response = client.get(fail_uri_with_params)

        if 'page_name' in params['query_params']:

            page_sample = reference_response.json[0].copy()
            page_filter = page_sample['pages']['three.com']
            page_sample['pages'] = { 'three.com':page_filter }

            assert success_response.json[0] == page_sample

            #Failed page result will return the rest of the
            #data associated with the test but results will be
            #empty
            assert fail_response.json == []

        else:

            assert success_response.json[0] == reference_response.json[0]
            assert fail_response.json == []

def test_get_metrics_summary(client, mtm, ptm, plm, monkeypatch):
    """
    Test the metrics data summary through the web service.
    """

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch, True)

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    total_tests = 3

    for index, revision in enumerate(setup_data['sample_revisions']):

        uri = ("/{0}/testdata/metrics/{1}/{2}/summary?"
              "product=Firefox&pushlog_project={3}")

        uri = uri.format(
            ptm.project, setup_data['branch'], revision, plm.project
            )

        response = client.get(uri)

        if revision == fail_revision:

            assert response.json['summary']['fail']['value'] == total_tests
            assert response.json['summary']['fail']['percent'] == 100

            assert response.json['summary']['pass']['value'] == 0
            assert response.json['summary']['pass']['percent'] == 0

        elif revision == skip_revision:
            assert 'summary' not in response.json
        else:
            if index > 0:
                assert response.json['summary']['fail']['value'] == 0
                assert response.json['summary']['fail']['percent'] == 0

                assert response.json['summary']['pass']['value'] == \
                    total_tests
                assert response.json['summary']['pass']['percent'] == 100

def test_get_metrics_summary_with_parameters(
    client, mtm, ptm, plm, monkeypatch
    ):
    """
    Test the metrics data summary with all available query parameters.
    """

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch, True)

    metric_values = get_metric_values()

    sample_data = TestData(perftest_data())

    sample_data['test_build']['branch'] = setup_data['branch']
    parameters = _get_uri_parameters(sample_data)

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    revision = setup_data['sample_revisions'][3]

    uri = ("/{0}/testdata/metrics/{1}/{2}/summary?"
           "product=Firefox&pushlog_project={3}")

    uri = uri.format(
        ptm.project, setup_data['branch'], revision, plm.project
        )

    reference_response = client.get(uri)
    platform = 'linux Ubuntu 11.10 x86_64'

    for params in parameters:

        if 'page_name' in params['query_params']:
            continue

        uri_with_params = "{0}&{1}".format(
            uri, params['query_params']
            )
        fail_uri_with_params = "{0}&{1}".format(
            uri, params['fail_params']
            )

        success_response = client.get(uri_with_params)
        fail_response = client.get(fail_uri_with_params)


        assert success_response.json == reference_response.json
        assert 'summary' not in fail_response.json

def test_get_metrics_pushlog(client, mtm, ptm, plm, monkeypatch):
    """
    Test the metrics pushlog through the web service.
    """

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch, True)

    target_revision_index = setup_data['target_revision_index']
    revision = setup_data['sample_revisions'][target_revision_index]

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    uri = "/{0}/testdata/metrics/{1}/{2}/pushlog?".format(
        ptm.project, setup_data['branch'], revision)

    uri_and_params = (
        "{0}product=Firefox&pushes_before=5&"
        "pushes_after=5&test_name={1}&pushlog_project={2}"
        "&page_name={3}"
        )

    uri_and_params = uri_and_params.format(
         uri, "Talos tp5r", plm.project, "one.com"
        )

    response = client.get(uri_and_params)

    match_count = 0

    metric_values = get_metric_values()

    for push in response.json:

        if push['dz_revision']:

            match_count += 1

            last_index = len(push['revisions']) - 1

            assert push['revisions'][last_index]['revision'] == \
                push['dz_revision']

            for data in push['metrics_data']:
                for page_data in data['pages']:
                    metric_data_keys = data['pages'][page_data].keys()
                    assert metric_values.issubset(metric_data_keys)

    assert match_count == 2


def _get_uri_parameters(sample_data):
    """
    Build a list of dictionaries containing all available
    query parameters for web service methods.
    """

    parameters = []

    os_name = sample_data['test_machine']['os']

    parameters.append(
        {
            'query_params':'os_name={0}'.format(os_name),
            'fail_params':'os_name=unicorn',
        })

    os_version = sample_data['test_machine']['osversion']

    parameters.append(
        {
            'query_params':'os_version={0}'.format(os_version),
            'fail_params':'os_version=unicorn.1.0',
        })

    branch_version = sample_data['test_build']['version']

    parameters.append(
        {
            'query_params':'branch_version={0}'.format(branch_version),
            'fail_params':'branch_version=unicorn.2.0',
        })

    processor = sample_data['test_machine']['platform']

    parameters.append(
        {
            'query_params':'processor={0}'.format(processor),
            'fail_params':'processor=x86_unicorn',
        })

    test_name = sample_data['testrun']['suite']

    parameters.append(
        {
            'query_params':'test_name={0}'.format(test_name),
            'fail_params':'test_name=findtheunicorn',
        })

    page_name = 'three.com'

    parameters.append(
        {
            'query_params':'page_name={0}'.format(page_name),
            'fail_params':'page_name=findtheunicorn',
        })

    return parameters
