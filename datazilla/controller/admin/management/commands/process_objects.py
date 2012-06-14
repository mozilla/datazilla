import os
import json

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import DatazillaModel

"""
My task
---------
Write a cron that processes the key/value object store and loads the data in the RDBS.
This cron will be a call to "manage.py transfer_objects" command
Take a look at model.base.DatazillaModel.
You will need to add a new source entry for 'objectstore',
it will work in the same fashion as 'perftest'.

The sql associated with objectstore should be contained in it's own file in
datazilla/model/sql/objectstore.json.

    DatazillaModel methods that access 'objectstore' would access the appropriate data hub
    by calling self.sources["objectstore"].dhub.execute() with the appropriate arguments.

    You can see the complete interface available for execute in
    https://github.com/jeads/datasource/blob/master/README .

    You can also read some of the methods in DatazillaModel to get an idea of
    what you can do with execute().

Note: Now that there are two different data hubs the DatazillaModel.dhub class
property might not make sense, maybe we need one for each type of contenttype?
Either way, you basic work flow will be add SQL statements to objectstore.sql
and call them through DatazillaModel methods that you add.


The manage.py command will utilize DatazillaModel methods that you add to retrieve the
objects and you can just call the existing method, DatazillaModel.load_test_data() to
load the data into the schema.  You will need to remove the call to
self._set_test_data(json_data, ref_data) since this stores the data in the test_data table.
On that note we will also need to remove test_data from the schema and all of the databases
with the contenttype of "perftest".  Lets make that the last step in this story.
We will not be able to do that until we roll out these changes so that we don't break
the development database and webservice that's ingesting data from talos.  Any errors
generated will need to be stored in the objectstore table and associated with the
correct object.

The validation of the json and capture of any error messages will need to be done in the new
manage.py command that transfers the data using DatazillaModel method calls.

The manage.py command should take an argument --project projectname.  Take a look at the
manage command in datazilla/controller/admin/management/commands.  This should give you
some ideas about how to structure the new manage command for transferring data from the
objectstore to perftest.


"""

""" WIP, right now this is just copied from transfer_data.py """
class Command(BaseCommand):

    help = "Transfer json blobs from the key/value store, uncompacting" \
            "them appropriately to the appropriate database."

    option_list = BaseCommand.option_list + (
        make_option('--project',
                    action='store',
                    dest='project',
                    default=False,
                    help='Source project to pull data from: talos, ' +
                         'b2g, stoneridge, test etc...'),
        make_option('--loadlimit',
                    action='store',
                    dest='loadlimit',
                    default=1,
                    help='Number of JSON blobs to fetch per '+
                         'single iteration of uncompacting'),
        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=None,
                    help='Write json-encapsulated SQL query out for debugging'))


    def handle(self, *args, **options):

        project   = options.get('project')
        debug     = options.get('debug')
        loadlimit = options.get('loadlimit')

        if not loadlimit:
            loadlimit = 1

        if not project:
            print "ERROR: Enter a valid project name"
            quit()


        dm = DatazillaModel(project)

        json_blobs = dm.retrieve_test_data(loadlimit)

        for json_blob in json_blobs:

            ## Print only if debug, otherwise load into perftest db ##
            if options['debug']:
                self.stdout.write(str(json_blob)+'\n')
            else:
                dm.load_test_data(json_blob)

        dm.disconnect()
