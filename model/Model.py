#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
import sys
import os
import re

from datasource.bases.BaseHub import BaseHub
from datasource.hubs.MySQL import MySQL

class Model:

   def __init__(self, sqlFileName):

      self.DATAZILLA_DATABASE_NAME     = os.environ["DATAZILLA_DATABASE_NAME"]
      self.DATAZILLA_DATABASE_USER     = os.environ["DATAZILLA_DATABASE_USER"]
      self.DATAZILLA_DATABASE_PASSWORD = os.environ["DATAZILLA_DATABASE_PASSWORD"]
      self.DATAZILLA_DATABASE_HOST     = os.environ["DATAZILLA_DATABASE_HOST"]
      self.DATAZILLA_DATABASE_PORT     = os.environ["DATAZILLA_DATABASE_PORT"]

      self.sqlFileName = sqlFileName

      try:
         self.DEBUG = os.environ["DATAZILLA_DEBUG"] is not None
      except KeyError:
         self.DEBUG = False

      self.rootPath = os.path.dirname(os.path.abspath(__file__))

      ####
      #Configuration of datasource hub:
      #	1 Build the datasource struct
      # 	2 Add it to the BaseHub
      #	3 Instantiate a MySQL hub for all derived classes
      ####
      dataSource = { self.DATAZILLA_DATABASE_NAME : { "hub":"MySQL",
                                                      "master_host":{"host":self.DATAZILLA_DATABASE_HOST,
                                                                     "user":self.DATAZILLA_DATABASE_USER,
                                                                     "passwd":self.DATAZILLA_DATABASE_PASSWORD},
                                                                     "default_db":self.DATAZILLA_DATABASE_NAME,
                                                      "procs": ["%s%s%s" % (self.rootPath,  "/sql/", sqlFileName)]
                                                    } }
      BaseHub.addDataSource(dataSource)
      self.dhub = MySQL(self.DATAZILLA_DATABASE_NAME)

  def setData(self, statement, placeholders):

     self.dhub.execute(proc='graphs.inserts.' + statement,
                       debug_show=self.DEBUG,
                       placeholders=placeholders)

   def setDataAndGetId(self, statement, placeholders):

      self.setData(statement, placeholders)

      idIter = self.dhub.execute(proc='graphs.selects.get_last_insert_id',
                                  debug_show=self.DEBUG,
                                  return_type='iter')

      return idIter.getColumnData('id')

   def isNumber(self, s):
      try:
         float(s)
         return True
      except ValueError:
         return False

   def buildReplacement(self, colData):

      rep = "AND "

      for key in colData:
         if len(colData[key]) > 0:
            rep += key + ' IN (' + colData[key] + ') AND '

      rep = re.sub('AND\s+$', '', rep)

      return rep

   def disconnect(self):
      self.dhub.disconnect()

