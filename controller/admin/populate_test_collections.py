import os
import sys

from optparse import OptionParser
from datazilla.model.DatazillaModel import DatazillaModel

def loadTestCollection():

   gm = DatazillaModel('graphs.json')

   products = gm.getProducts('id')

   for productName in products:

      if products[ productName ]['product'] and \
         products[ productName ]['version'] and \
         products[ productName ]['branch']:

         name = "%s %s %s" % (products[ productName ]['product'],
                              products[ productName ]['version'],
                              products[ productName ]['branch'])

         id = gm.setData('set_test_collection', [ name, "", name ])
         gm.setData('set_test_collection_map', [ id, products[ productName ]['id'] ])

   gm.disconnect()

if __name__ == '__main__':

   usage = """usage: %prog [options] --load"""
   parser = OptionParser(usage=usage)

   parser.add_option('-l', 
                     '--load', 
                     action='store_true', 
                     dest='load',
                     default=False, 
                     type=None,
                     help="Identitfy new product branches and add them as test collections.")

   (options, args) = parser.parse_args()

   if options.load:
      loadTestCollection()
