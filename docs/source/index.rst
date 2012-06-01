.. datazilla documentation master file, created by
   sphinx-quickstart on Thu May 31 11:14:22 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Datazilla's documentation!
=====================================

Datazilla is a system for managing and visualizing data.

.. NOTE:: This is a work in progress and will likely see a number of structural changes. It is currently being developed to manage Talos test data, a performance testing framework developed by mozilla for testing software products.

Contents
---------

.. toctree::
   :maxdepth: 2

   installation
   architecture
   tests

* :ref:`search`

Description
-----------
The fundamental unit of data display in the user interface is called a *dataview*. Data views can display data in any number of tabular or graphical ways. Data views can also send signals to one another enabling the user to maintain visual context across multiple graphical displays of different data types. Each data view shares a toolbar that abstracts navigation, data presentation controls, and visual presentation. A prototype of datazilla was first developed in an application called bughunter.

This project includes a model, web service, and web based user interface, and eventually it will support a local development environment.

