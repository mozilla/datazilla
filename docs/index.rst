.. datazilla documentation master file, created by
   sphinx-quickstart on Thu May 31 11:14:22 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Datazilla's documentation!
=====================================

Datazilla is a system for managing and visualizing test data.  It's designed to be able to manage different subsets of test data, such as performance data.

Description
-----------
At a top level, performance test data is submitted as a JSON data structure to the webservice via http post, an example data structure can be found `here <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/template_schema/schema_perftest.json>`_.  It's stored in a dedicated database schema as an object, the objects in this schema are then translated into a relational database schema where individual fields in the JSON structure are indexed for queries.  The indexed data is used for applying statistical analysis to identify performance regressions.  Both the indexed data and un-processed objects are available through the web service.

New JSON objects and schema definitions can be added to support different types of data.  It's also possible to utilize the fields already available in the JSON structure to represent different information.

This project includes a model, web service, and web based user interfaces.

Contents
---------

.. toctree::
   :maxdepth: 3

   Web Services <webservice>
   installation
   development
   architecture

* :ref:`search`

