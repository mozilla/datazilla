"""
Functions for populating test collections.

"""
import itertools

from datazilla.model import PerformanceTestModel


def set_default_products(project):

    ptm = PerformanceTestModel(project)

    products = ptm.get_products('id')

    versions = [ products[id]['version'] for id in products ]

    #sort version strings
    versions.sort(
        key=lambda s: map(numeric_prefix, s.split('.')), reverse=True
        )

    if versions:

        current_version = versions[0]

        default_products = []
        for id in products:
            default = 0
            if current_version == products[id]['version']:
                default = 1

        ptm.set_default_product(id, default)

        ptm.cache_default_project()

def numeric_prefix(s):
    n = 0
    for c in s:
        if not c.isdigit():
            return n
        else:
            n = n * 10 + int(c)
    return n

def get_current_version(i, args):

    products = args[0]
    current_version = args[1]

    if products[i]['version'] == current_version:
        return products[i]
