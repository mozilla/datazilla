"""
Functions for populating test collections.

"""
from MySQLdb import IntegrityError

from datazilla.model import PerformanceTestModel


def load_test_collection(project):

    ptm = PerformanceTestModel(project)

    products = ptm.get_products('id')

    product_names = {}

    for id in products:

        if products[ id ]['product'] and \
           products[ id ]['version'] and \
           products[ id ]['branch']:

            name = get_test_collection_name(
                products[ id ]['product'],
                products[ id ]['version'],
                products[ id ]['branch']
                )

            product_names[name] = id

    test_collection_names = ptm.get_test_collection_set()

    new_name_set = set(
        product_names.keys()
        ).difference( test_collection_names )

    for new_name in new_name_set:
        id = ptm.set_test_collection(new_name, "")
        ptm.set_test_collection_map(id, product_names[ new_name ])

    ptm.disconnect()

def get_test_collection_name(product, version, branch):
    name = "%s %s %s" % (product, version, branch)
    return name
