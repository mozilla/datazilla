import sys, os

from datazilla.vendor import add_vendor_lib
add_vendor_lib()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")

from optparse import OptionParser
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

if __name__ == '__main__':

    usage = """usage: %prog [options] --load"""
    parser = OptionParser(usage=usage)

    parser.add_option('-p',
                      '--project',
                      action='store',
                      dest='project',
                      default=False,
                      type='string',
                      help="Set the project to run on: talos, b2g, schema, test etc....")

    parser.add_option('-l',
                      '--load',
                      action='store_true',
                      dest='load',
                      default=False,
                      type=None,
                      help="Identitfy new product branches and add them as test collections.")

    (options, args) = parser.parse_args()

    if not options.project:
        print "No project argument provided."
        print parser.usage
        sys.exit(0)

    if options.load:
        load_test_collection(options.project)
