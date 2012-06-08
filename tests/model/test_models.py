def pytest_funcarg__dm(request):
    from datazilla.model import DatazillaModel
    return DatazillaModel("talos")


def test_get_operating_systems(dm):
    test_data = dm.get_operating_systems()


def test_get_tests(dm):
    test_data = dm.get_tests()


def test_get_products(dm):
    test_data = dm.get_products()


def test_get_machines(dm):
    test_data = dm.get_machines()


def test_get_options(dm):
    test_data = dm.get_options()


def test_get_pages(dm):
    test_data = dm.get_pages()


def test_get_aux_data(dm):
    test_data = dm.get_aux_data()


def test_get_ref(dm):
    test_data = dm.get_reference_data()


def test_get_test_collections(dm):
    test_data = dm.get_test_collections()


def test_get_test_reference_data(dm):
    test_data = dm.get_test_reference_data()


def test_get_product_test_os_map(dm):
    test_data = dm.get_product_test_os_map()


def test_get_summary_cache(dm):
    cache_data = dm.get_summary_cache(10, 'days_30')
