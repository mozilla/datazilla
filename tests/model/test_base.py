import pytest

from ..sample_data import perftest_json, perftest_data


def test_unicode(dm):
    """Unicode representation of a ``DatazillaModel`` is the project name."""
    assert unicode(dm) == u"testproj"


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
    from datazilla.model import DatazillaModel
    dm2 = DatazillaModel("testproj")

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
    data = {'testrun': {'suite': 'talos'}}

    first_id = dm._get_or_create_test_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_test_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_test_id_no_testrun(dm):
    """Raises TestDataError if there is no 'testrun' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_test_id({})

    assert str(e.value) == "Missing 'testrun' key."


def test_get_or_create_test_id_no_suite_name(dm):
    """Raises TestDataError if there is no 'suite' key in data['testrun']."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_test_id({'testrun': {}})

    assert str(e.value) == "Testrun missing 'suite' key."


def test_get_or_create_test_id_bad_version(dm):
    """Raises TestDataError if the 'suite_version' key is not an integer."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_test_id(
            {'testrun': {'suite': 'talos', 'suite_version': 'foo'}})

    assert str(e.value) == "Testrun 'suite_version' is not an integer."


def test_get_or_create_option_ids(dm):
    """Returns dictionary of option IDs from db (creating if needed)."""
    data = {'testrun': {'options': ['option1', 'option2']}}

    first_ids = dm._get_or_create_option_ids(data)

    # second call returns same id for same options
    data['testrun']['options'].append('option3')
    second_ids = dm._get_or_create_option_ids(data)

    assert first_ids['option1'] == second_ids['option1']
    assert first_ids['option2'] == second_ids['option2']
    assert set(second_ids.keys()) == set(['option1', 'option2', 'option3'])


def test_get_or_create_option_ids_no_testrun(dm):
    """Raises TestDataError if there is no 'testrun' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_option_ids({})

    assert str(e.value) == "Missing 'testrun' key."


def test_get_or_create_option_ids_bad_options(dm):
    """Raises TestDataError if the 'options' key is not a list."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_option_ids({'testrun': {'options': 'foo'}})

    assert str(e.value) == "Testrun 'options' is not a list."


def test_get_or_create_os_id(dm):
    """Returns OS id for the given test-machine (creating it if needed)."""
    data = {'test_machine': {'os': 'linux', 'osversion': 'Ubuntu 11.10'}}

    first_id = dm._get_or_create_os_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_os_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_os_id_no_test_machine(dm):
    """Raises TestDataError if there is no 'test_machine' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_os_id({})

    assert str(e.value) == "Missing 'test_machine' key."


def test_get_or_create_os_id_no_os(dm):
    """Raises TestDataError if there is no 'os' key in data['test_machine']."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_os_id({'test_machine': {'osversion': '7'}})

    assert str(e.value) == "Test machine missing 'os' key."


def test_get_or_create_os_id_no_osversion(dm):
    """Raises TestDataError if 'osversion' missing from 'test_machine'."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_os_id({'test_machine': {'os': 'linux'}})

    assert str(e.value) == "Test machine missing 'osversion' key."


def test_get_or_create_product_id(dm):
    """Returns product id for the given build (creating it if needed)."""
    data = {
        'test_build': {
            'name': 'Firefox', 'branch': 'Mozilla-Aurora', 'version': '14.0a2'}
        }

    first_id = dm._get_or_create_product_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_product_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_product_id_no_test_build(dm):
    """Raises TestDataError if there is no 'test_build' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_product_id({})

    assert str(e.value) == "Missing 'test_build' key."


def test_get_or_create_product_id_no_name(dm):
    """Raises TestDataError if there is no 'name' key in data['test_build']."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_product_id(
            {'test_build': {'branch': 'Mozilla-Aurora', 'version': '14.0a2'}})

    assert str(e.value) == "Test build missing 'name' key."


def test_get_or_create_product_id_no_branch(dm):
    """Raises TestDataError if there is no 'branch' in data['test_build']."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_product_id(
            {'test_build': {'name': 'Firefox', 'version': '14.0a2'}})

    assert str(e.value) == "Test build missing 'branch' key."


def test_get_or_create_product_id_no_version(dm):
    """Raises TestDataError if there is no 'version' in data['test_build']."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_product_id(
            {'test_build': {'name': 'Firefox', 'branch': 'Mozilla-Aurora'}})

    assert str(e.value) == "Test build missing 'version' key."


def test_get_or_create_machine_id(dm):
    """Returns machine id for the given test data (creating it if needed)."""
    data = {'test_machine': {'name': 'qm-pxp01'}}

    first_id = dm._get_or_create_machine_id(data)

    inserted_id = dm._get_last_insert_id()

    # second call with same data returns existing id
    second_id = dm._get_or_create_machine_id(data)

    assert second_id == first_id == inserted_id


def test_get_or_create_machine_id_no_test_machine(dm):
    """Raises TestDataError if there is no 'test_machine' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_machine_id({})

    assert str(e.value) == "Missing 'test_machine' key."


def test_get_or_create_machine_id_no_name(dm):
    """Raises TestDataError if there is no 'name' in data['test_machine']."""
    with pytest.raises(dm.TestDataError) as e:
        dm._get_or_create_machine_id({'test_machine': {}})

    assert str(e.value) == "Test machine missing 'name' key."


def test_set_build_data(dm):
    """Inserts data into the build table."""
    data = perftest_data()

    os_id = dm._get_or_create_os_id(data)
    product_id = dm._get_or_create_product_id(data)
    machine_id = dm._get_or_create_machine_id(data)

    build_id = dm._set_build_data(data, os_id, product_id, machine_id)

    row_data = dm.sources["perftest"].dhub.execute(
        proc="perftest_test.selects.build", placeholders=[build_id])[0]

    assert row_data["test_build_id"] == data["test_build"]["id"]
    assert row_data["operating_system_id"] == os_id
    assert row_data["product_id"] == product_id
    assert row_data["machine_id"] == machine_id
    assert row_data["processor"] == data["test_machine"]["platform"]
    assert row_data["revision"] == data["test_build"]["revision"]


def test_set_build_data_no_test_machine(dm):
    """Raises TestDataError if there is no 'test_machine' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._set_build_data(
            {"test_build": {"id": "12345", "revision": "deadbeef"}},
             None, None, None,
             )

    assert str(e.value) == "Missing 'test_machine' key."


def test_set_build_data_no_test_build(dm):
    """Raises TestDataError if there is no 'test_build' key in data."""
    with pytest.raises(dm.TestDataError) as e:
        dm._set_build_data(
            {"test_machine": {"platform": "arm"}}, None, None, None)

    assert str(e.value) == "Missing 'test_build' key."


def test_set_build_data_no_platform(dm):
    """Raises TestDataError if 'test_machine' is missing 'platform' key."""
    with pytest.raises(dm.TestDataError) as e:
        dm._set_build_data(
            {
                "test_build": {"id": "12345", "revision": "deadbeef"},
                "test_machine": {},
                },
             None, None, None,
             )

    assert str(e.value) == "Test machine missing 'platform' key."


def test_set_build_data_no_build_id(dm):
    """Raises TestDataError if 'test_machine' is missing 'platform' key."""
    with pytest.raises(dm.TestDataError) as e:
        dm._set_build_data(
            {
                "test_build": {"revision": "deadbeef"},
                "test_machine": {"platform": "arm"},
                },
             None, None, None,
             )

    assert str(e.value) == "Test build missing 'id' key."



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


def test_get_ref(dm):
    dm.get_reference_data()


def test_get_test_collections(dm):
    dm.get_test_collections()


def test_get_test_reference_data(dm):
    dm.get_test_reference_data()


def test_get_product_test_os_map(dm):
    dm.get_product_test_os_map()


def test_get_summary_cache(dm):
    dm.get_summary_cache(10, 'days_30')
