import pytest
import json

from datazilla.model.base import TestDataError, TestData

from ..sample_data import perftest_json, perftest_data, perftest_ref_data_json


def test_unicode(dm):
    """Unicode representation of a ``PerformanceTestModel`` is the project name."""
    assert unicode(dm) == u"testproj"


def test_disconnect(dm):
    """test that you model disconnects"""

    # establish the connection to perftest.
    dm._get_last_insert_id()
    # establish the connection to objectstore
    dm.retrieve_test_data(limit=1)

    dm.disconnect()
    for src in dm.sources.itervalues():
        assert src.dhub.connection["master_host"]["con_obj"].open == False


def test_claim_objects(dm):
    """``claim_objects`` claims & returns unclaimed rows up to a limit."""
    blobs = [
        perftest_json(testrun={"date": "1330454755"}),
        perftest_json(testrun={"date": "1330454756"}),
        perftest_json(testrun={"date": "1330454757"}),
        ]

    for blob in blobs:
        dm.store_test_data(blob)

    rows1 = dm.claim_objects(2)

    # a separate worker with a separate connection
    from datazilla.model import PerformanceTestModel
    dm2 = PerformanceTestModel("testproj")

    rows2 = dm2.claim_objects(2)

    loading_rows = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.counts.loading")[0]["loading_count"]

    assert len(rows1) == 2
    # second worker asked for two rows but only got one that was left
    assert len(rows2) == 1

    # all three blobs were fetched by one of the workers
    assert set([r["json_blob"] for r in rows1 + rows2]) == set(blobs)

    # the blobs are all marked as "loading" in the database
    assert loading_rows == 3


def test_mark_object_complete(dm):
    """Marks claimed row complete and records run id."""
    dm.store_test_data(perftest_json())
    row_id = dm.claim_objects(1)[0]["id"]
    test_run_id = 7 # any arbitrary number; no cross-db constraint checks

    dm.mark_object_complete(row_id, test_run_id)

    row_data = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.selects.row", placeholders=[row_id])[0]

    assert row_data["test_run_id"] == test_run_id
    assert row_data["processed_flag"] == "complete"


def test_get_or_create_test_id(dm):
    """Returns test id for the given test-run suite (creating it if needed)."""
    data = TestData({'testrun': {'suite': 'talos'}})

    first_id = dm._get_or_create_test_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_test_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_test_id_no_testrun(dm):
    """Raises TestDataError if there is no 'testrun' key in data."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_test_id(TestData({}))

    assert str(e.value) == "Missing data: ['testrun']."


def test_get_or_create_test_id_no_suite_name(dm):
    """Raises TestDataError if there is no 'suite' key in data['testrun']."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_test_id(TestData({'testrun': {}}))

    assert str(e.value) == "Missing data: ['testrun']['suite']."


def test_get_or_create_test_id_bad_version(dm):
    """Raises TestDataError if the 'suite_version' key is not an integer."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_test_id(
            TestData({'testrun': {'suite': 'talos', 'suite_version': 'foo'}}))

    expected = "Bad value: ['testrun']['suite_version'] is not an integer."
    assert str(e.value) == expected


def test_get_or_create_option_ids(dm):
    """Returns option ID from db for given option (creating if needed)."""
    first_id = dm._get_or_create_option_id('option1')

    inserted_id = dm._get_last_insert_id()

    # second call returns same id for same option
    second_id = dm._get_or_create_option_id('option1')

    assert first_id == second_id == inserted_id


def test_get_or_create_os_id(dm):
    """Returns OS id for the given test-machine (creating it if needed)."""
    data = TestData(
        {'test_machine': {'os': 'linux', 'osversion': 'Ubuntu 11.10'}})

    first_id = dm._get_or_create_os_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_os_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_os_id_no_test_machine(dm):
    """Raises TestDataError if there is no 'test_machine' key in data."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_os_id(TestData({}))

    assert str(e.value) == "Missing data: ['test_machine']."


def test_get_or_create_os_id_no_os(dm):
    """Raises TestDataError if there is no 'os' key in data['test_machine']."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_os_id(TestData({'test_machine': {'osversion': '7'}}))

    assert str(e.value) == "Missing data: ['test_machine']['os']."


def test_get_or_create_os_id_no_osversion(dm):
    """Raises TestDataError if 'osversion' missing from 'test_machine'."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_os_id(TestData({'test_machine': {'os': 'linux'}}))

    assert str(e.value) == "Missing data: ['test_machine']['osversion']."


def test_get_or_create_product_id(dm):
    """Returns product id for the given build (creating it if needed)."""
    data = TestData(
        {
            'test_build': {
                'name': 'Firefox',
                'branch': 'Mozilla-Aurora',
                'version': '14.0a2'}
            }
        )

    first_id = dm._get_or_create_product_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_product_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_product_id_no_test_build(dm):
    """Raises TestDataError if there is no 'test_build' key in data."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_product_id(TestData({}))

    assert str(e.value) == "Missing data: ['test_build']."


def test_get_or_create_product_id_no_name(dm):
    """Raises TestDataError if there is no 'name' key in data['test_build']."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_product_id(
            TestData(
                {
                    'test_build': {
                        'branch': 'Mozilla-Aurora',
                        'version': '14.0a2',
                        },
                    }
                )
            )

    assert str(e.value) == "Missing data: ['test_build']['name']."


def test_get_or_create_product_id_no_branch(dm):
    """Raises TestDataError if there is no 'branch' in data['test_build']."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_product_id(
            TestData({'test_build': {'name': 'Firefox', 'version': '14.0a2'}}))

    assert str(e.value) == "Missing data: ['test_build']['branch']."


def test_get_or_create_product_id_no_version(dm):
    """Raises TestDataError if there is no 'version' in data['test_build']."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_product_id(
            TestData(
                {'test_build': {'name': 'Firefox', 'branch': 'Mozilla-Aurora'}}
                )
            )

    assert str(e.value) == "Missing data: ['test_build']['version']."


def test_get_or_create_machine_id(dm):
    """Returns machine id for the given test data (creating it if needed)."""
    os_data = TestData(
        {'test_machine': {'os': 'linux', 'osversion': 'Ubuntu 11.10'}})

    os_id = dm._get_or_create_os_id(os_data)

    data = TestData({'test_machine': {'name': 'qm-pxp01'}})

    first_id = dm._get_or_create_machine_id(data, os_id)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_machine_id(data, os_id)

    assert second_id == first_id == inserted_id


def test_get_or_create_machine_id_no_test_machine(dm):
    """Raises TestDataError if there is no 'test_machine' key in data."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_machine_id(TestData({}), None)

    assert str(e.value) == "Missing data: ['test_machine']."


def test_get_or_create_machine_id_no_name(dm):
    """Raises TestDataError if there is no 'name' in data['test_machine']."""
    with pytest.raises(TestDataError) as e:
        dm._get_or_create_machine_id(TestData({'test_machine': {}}), None)

    assert str(e.value) == "Missing data: ['test_machine']['name']."


def test_set_build_data(dm):
    """Inserts data into the build table."""
    data = TestData(perftest_data())

    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)

    build_id = dm._set_build_data(data, product_id)

    row_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.build", placeholders=[build_id])[0]

    assert row_data["test_build_id"] == data["test_build"]["id"]
    assert row_data["product_id"] == product_id
    assert row_data["processor"] == data["test_machine"]["platform"]
    assert row_data["revision"] == data["test_build"]["revision"]


def test_set_build_data_no_test_machine(dm):
    """Raises TestDataError if there is no 'test_machine' key in data."""
    with pytest.raises(TestDataError) as e:
        dm._set_build_data(
            TestData({"test_build": {"id": "12345", "revision": "deadbeef"}}),
            None
            )

    assert str(e.value) == "Missing data: ['test_machine']."


def test_set_build_data_no_test_build(dm):
    """Raises TestDataError if there is no 'test_build' key in data."""
    with pytest.raises(TestDataError) as e:
        dm._set_build_data(
            TestData({"test_machine": {"platform": "arm"}}), None)

    assert str(e.value) ==  "Missing data: ['test_build']."


def test_set_build_data_no_platform(dm):
    """Raises TestDataError if 'test_machine' is missing 'platform' key."""
    with pytest.raises(TestDataError) as e:
        dm._set_build_data(
            TestData(
                {
                    "test_build": {"id": "12345", "revision": "deadbeef"},
                    "test_machine": {},
                    }
                ),
             None
             )

    assert str(e.value) == "Missing data: ['test_machine']['platform']."


def test_set_build_data_no_build_id(dm):
    """Raises TestDataError if 'test_machine' is missing 'platform' key."""
    with pytest.raises(TestDataError) as e:
        dm._set_build_data(
            TestData(
                {
                    "test_build": {"revision": "deadbeef"},
                    "test_machine": {"platform": "arm"},
                    }
                ),
             None
             )

    assert str(e.value) == "Missing data: ['test_build']['id']."


def test_set_test_run_data(dm):
    """Inserts data into the test_run table."""
    data = TestData(perftest_data())

    test_id = dm._get_or_create_test_id(data)
    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data, os_id)

    build_id = dm._set_build_data(data, product_id)

    test_run_id = dm._set_test_run_data(data, test_id, build_id, machine_id)

    row_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.test_run", placeholders=[test_run_id])[0]

    assert row_data["test_id"] == test_id
    assert row_data["build_id"] == build_id
    assert row_data["revision"] == data["test_build"]["revision"]
    assert row_data["date_run"] == int(data["testrun"]["date"])


def test_set_test_run_data_bad_date(dm):
    """Raises TestDataError if the testrun 'date' key is not an integer."""
    with pytest.raises(TestDataError) as e:
        dm._set_test_run_data(
            TestData({'testrun': {'date': 'foo'}}),
            None, None, None
            )

    expected = "Bad value: ['testrun']['date'] is not an integer."
    assert str(e.value) == expected


def test_set_option_data(dm):
    """Inserts options in the db."""
    data = TestData(perftest_data(testrun={'options': {'opt': 'val'}}))

    # Create all the prerequisites for getting a test_run_id
    test_id = dm._get_or_create_test_id(data)
    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data, os_id)

    build_id = dm._set_build_data(data, product_id)
    test_run_id = dm._set_test_run_data(data, test_id, build_id, machine_id)

    # Try to set the option data
    dm._set_option_data(data, test_run_id)

    row_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.option_value",
        placeholders=['opt', test_run_id],
        )[0]

    assert row_data['value'] == 'val'

def test_set_extension_data(dm):
    """Confirms that options named 'extensions' are ignored
       while other option names are inserted.

       TODO: This will be modified to test insertion of extension data
       into the schema."""
    options = {'options':{'extensions':[{"name":"ext1"},
                                       {"name":"ext2"},
                                       {"name":"ext3"}],
                         'name':'value'}}

    data = TestData(perftest_data(testrun=options))

    # Create all the prerequisites for getting a test_run_id
    test_id = dm._get_or_create_test_id(data)
    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data, os_id)

    build_id = dm._set_build_data(data, product_id)

    test_run_id = dm._set_test_run_data(data, test_id, build_id, machine_id)

    # Try to set the option data
    dm._set_option_data(data, test_run_id)

    # Retrieve any options named 'extensions'
    option_name_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.option_name",
        placeholders=['extensions'])

    # Make sure we don't get any data back for the 
    # option name 'extensions'
    assert option_name_data == ()

    # Retrieve option values for the 'name' option
    option_value_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.option_value",
        placeholders=['name', test_run_id],
        )[0]

    # Confirm that we get a value for the 'name' options
    assert option_value_data['value'] == 'value'

def test_set_test_values(dm):
    """Inserts test results in the db."""
    data = TestData(perftest_data(results={"example.com": [1, 2, 3]}))

    # Create all the prerequisites for getting a test_run_id
    test_id = dm._get_or_create_test_id(data)
    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data, os_id)

    build_id = dm._set_build_data(data, product_id)

    test_run_id = dm._set_test_run_data(data, test_id, build_id, machine_id)

    # Try to set the test values
    dm._set_test_values(data, test_id, test_run_id)

    page_row = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.pages",
        placeholders=[test_id],
        )[0]

    value_rows = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.test_values",
        placeholders=[test_run_id],
        )
    enumerated_values = set([(r['run_id'], r['value']) for r in value_rows])


    assert page_row['url'] == 'example.com'
    assert enumerated_values == set([(1, 1), (2, 2), (3, 3)])
    assert set([r['page_id'] for r in value_rows]) == set([page_row['id']])


def test_set_test_aux_data(dm):
    """Inserts test auxiliary data in the db."""
    data = TestData(perftest_data(results_aux={"foo": [1, 2, "three"]}))

    # Create all the prerequisites for getting a test_run_id
    test_id = dm._get_or_create_test_id(data)
    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data, os_id)

    build_id = dm._set_build_data(data, product_id)

    test_run_id = dm._set_test_run_data(data, test_id, build_id, machine_id)

    # Try to set the aux data
    dm._set_test_aux_data(data, test_id, test_run_id)

    aux_row = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.aux_data",
        placeholders=[test_id],
        )[0]

    test_aux_rows = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.test_aux",
        placeholders=[test_run_id],
        )
    enumerated_values = set(
        [
            (r['run_id'], r['numeric_data'], r['string_data'])
            for r in test_aux_rows
            ]
        )
    aux_data_ids = set([r['aux_data_id'] for r in test_aux_rows])


    assert aux_row['name'] == 'foo'
    assert enumerated_values == set([(1, 1, ""), (2, 2, ""), (3, 0, "three")])
    assert aux_data_ids == set([aux_row['id']])


def test_load_test_data(dm):
    """Loads a TestData instance into db and returns test_run_id."""
    data = TestData(perftest_data())
    test_run_id = dm.load_test_data(data)

    test_run_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.test_run", placeholders=[test_run_id])[0]

    value_rows = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.test_values",
        placeholders=[test_run_id],
        )
    distinct_pages = set([r['page_id'] for r in value_rows])

    # We just spot-check here, since all the methods that do the heavy lifting
    # are individually tested.
    assert test_run_data["revision"] == data["test_build"]["revision"]
    assert test_run_data["date_run"] == int(data["testrun"]["date"])
    assert len(distinct_pages) == len(data["results"])


def test_process_objects(dm):
    """Claims and processes a chunk of unprocessed JSON test data blobs."""
    # Load some rows into the objectstore
    blobs = [
        perftest_json(testrun={"date": "1330454755"}),
        perftest_json(testrun={"date": "1330454756"}),
        perftest_json(testrun={"date": "1330454757"}),
        ]

    for blob in blobs:
        dm.store_test_data(blob)

    # just process two rows
    dm.process_objects(2)

    test_run_rows = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.test_runs")
    date_set = set([r['date_run'] for r in test_run_rows])
    expected_dates = set([1330454755, 1330454756, 1330454757])

    complete_count = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.counts.complete")[0]["complete_count"]
    loading_count = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.counts.loading")[0]["loading_count"]

    assert complete_count == 2
    assert loading_count == 0
    assert date_set.issubset(expected_dates)
    assert len(date_set) == 2


def test_process_objects_invalid_json(dm):
    dm.store_test_data("invalid json")
    row_id = dm._get_last_insert_id("objectstore")

    dm.process_objects(1)

    row_data = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.selects.row", placeholders=[row_id])[0]

    expected_error = "Malformed JSON: No JSON object could be decoded"

    assert row_data['error_flag'] == 'Y'
    assert row_data['error_msg'] == expected_error
    assert row_data['processed_flag'] == 'ready'


def test_process_objects_unknown_error(dm, monkeypatch):
    dm.store_test_data("{}")
    row_id = dm._get_last_insert_id("objectstore")

    # force an unexpected error to occur
    def raise_error(*args, **kwargs):
        raise ValueError("Something blew up!")
    monkeypatch.setattr(dm, "load_test_data", raise_error)

    dm.process_objects(1)

    row_data = dm.sources["objectstore"].dhub.execute(
        proc="objectstore_test.selects.row", placeholders=[row_id])[0]

    expected_error_msg = "Unknown error: ValueError: Something blew up!"

    assert row_data['error_flag'] == 'Y'
    assert row_data['error_msg'] == expected_error_msg
    assert row_data['processed_flag'] == 'ready'


def test_get_test_reference_data(dm):

    data = TestData(perftest_data())

    ##Insert reference data from perftest_data##
    test_id = dm._get_or_create_test_id(data)
    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data, os_id)

    build_id = dm._set_build_data(data, product_id)
    test_run_id = dm._set_test_run_data(data, test_id, build_id, machine_id)

    json_data = json.loads( dm.get_test_reference_data('testproj-refdata') )

    ##Retrieve reference data structure built from perttest_data##
    ref_data_json = json.loads( perftest_ref_data_json() )

    assert json_data == ref_data_json


def test_get_default_product(dm):

    data = TestData(
        {
            'test_build': {
                'name': 'Firefox',
                'branch': 'Mozilla-Aurora',
                'version': '14.0a2'}
            }
        )

    id = dm._get_or_create_product_id(data)

    dm.set_default_product(id)

    default_product = dm.get_default_product()

    assert default_product['product'] == 'Firefox'
    assert default_product['branch'] == 'Mozilla-Aurora'
    assert default_product['version'] == '14.0a2'


# TODO fill in the following tests:

def test_get_operating_systems(dm):
    dm.get_operating_systems()


def test_get_tests(dm):
    dm.get_tests()


def test_get_products(dm):
    dm.get_products()


def test_get_machines(dm):
    dm.get_machines()


def test_get_options(dm):
    dm.get_options()


def test_get_pages(dm):
    dm.get_pages()


def test_get_aux_data(dm):
    dm.get_aux_data()


def test_get_test_collections(dm):
    dm.get_test_collections()




def test_get_product_test_os_map(dm):
    dm.get_product_test_os_map()


def test_get_summary_cache(dm):
    dm.get_summary_cache(10, 'days_30')
