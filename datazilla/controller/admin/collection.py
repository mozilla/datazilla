"""
Functions for populating test collections.

"""
from datazilla.model import DatazillaModel


def load_test_collection(project):

    dm = DatazillaModel(project)

    products = dm.get_products('id')

    for product_name in products:

        if products[ product_name ]['product'] and \
           products[ product_name ]['version'] and \
           products[ product_name ]['branch']:

            name = "%s %s %s" % (products[ product_name ]['product'],
                                 products[ product_name ]['version'],
                                 products[ product_name ]['branch'])

            id = dm.set_test_collection(name, "")
            dm.set_test_collection_map(id, products[ product_name ]['id'])

    dm.disconnect()
