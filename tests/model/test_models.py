def pytest_funcarg__dm(request):
    from datazilla.model import DatazillaModel
    return DatazillaModel("talos")


def testGetOperatingSystems(dm):
    testData = dm.getOperatingSystems()


def testGetTests(dm):
    testData = dm.getTests()


def testGetProducts(dm):
    testData = dm.getProducts()


def testGetMachines(dm):
    testData = dm.getMachines()


def testGetOptions(dm):
    testData = dm.getOptions()


def testGetPages(dm):
    testData = dm.getPages()


def testGetAuxData(dm):
    testData = dm.getAuxData()


def testGetRef(dm):
    testData = dm.getReferenceData()


def testGetTestCollections(dm):
    testData = dm.getTestCollections()


def testGetTestReferenceData(dm):
    testData = dm.getTestReferenceData()


def testGetProductTestOsMap(dm):
    testData = dm.getProductTestOsMap()


def testGetSummaryCache(dm):
    cacheData = dm.getSummaryCache(10, 'days_30')
