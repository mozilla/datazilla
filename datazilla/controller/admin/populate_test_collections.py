import sys, os

from datazilla.vendor import add_vendor_lib
add_vendor_lib()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")

from optparse import OptionParser
from datazilla.model import DatazillaModel

def loadTestCollection(project):

    dm = DatazillaModel(project)

    products = dm.getProducts('id')

    for productName in products:

        if products[ productName ]['product'] and \
           products[ productName ]['version'] and \
           products[ productName ]['branch']:

            name = "%s %s %s" % (products[ productName ]['product'],
                                 products[ productName ]['version'],
                                 products[ productName ]['branch'])

            id = dm.set_test_collection(name, "")
            dm.set_test_collection_map(id, products[ productName ]['id'])

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
        loadTestCollection(options.project)
