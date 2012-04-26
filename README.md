#Datazilla
Datazilla is a system for managing and visualizing data.  The fundamental unit of data display in the user interface is called a data view.  Data views can display data in any number of ways: tabular or graphical.  Data views can also send signals to one another enabling the user to maintain visual context across multiple graphical displays of different data types.  Each data view shares a toolbar that abstracts navigation, data presentation controls, and visual presentation.  A prototype of datazilla was first developed in an application called [bughunter] [1].

This project includes a model, webservice, and web based user interface, and eventually it will support a local development environment. 

This is a work in progress and will likely see a number of structural changes.  It is currently being developed to manage [Talos] [2] test data, a performance testing framework developed by mozilla for testing software products.

##Architecture
At a top level datazilla can be described with three different parts: model, webservice, and UI.

###Model
The model layer is found in datazilla/model and provides an interface for getting/setting data in a database.  The datazilla model classes rely on a module called [datasource] [5].  This module encapsulates SQL manipulation.  All of the SQL used by the system is stored in a JSON file found in /datazilla/model/[sql] [6].  There can be any number of SQL files stored in this format.  The JSON structure allows SQL to be stored in named associative arrays that also contain the host type to be associated with each statement.  Any command line script or webservice method that requires data should use a derived model class to obtain it.

```python
gm = DatazillaModel('graphs.json')
products = gm.getProductTestOsMap()
```

The gm.getProductTestOsMap() method looks like
```python
   def getProductTestOsMap(self):

      productTuple = self.dhub.execute(proc='graphs.selects.get_product_test_os_map',
                                       debug_show=self.DEBUG,
                                       return_type='tuple') 

      return productTuple
```

graphs.selects.get_product_test_os_map found in datazilla/model/sql/graphs.json looks like
```json
   "selects":{

      ...other SQL statements...

      "get_product_test_os_map":{

         "sql":"SELECT b.product_id, tr.test_id, b.operating_system_id 
                FROM test_run AS tr
                LEFT JOIN build AS b ON tr.build_id = b.id 
                WHERE b.product_id IN (
                  SELECT product_id
                  FROM product )
               GROUP BY b.product_id, tr.test_id, b.operating_system_id",

          "host":"master_host"
      },

```
The string, 'graphs', in 'graphs.selects.get_product_test_os_map' refers to the file name.  The SQL in graphs.json can be written with placeholders and a string replacement system, see [datasource] [5] for all of the features available.

If you're thinking why not just use an ORM?  I direct you to [seldo.com] [9] where you will find an excellent answer to your question that I completely agree with.  It has been my experience that ORMs don't scale well with data models that need to scale horizontally.  They also fail to represent relational data accurately in OOP like objects.  If you can represent your data model with objects, then use an object store not an RDBS.  SQL answers questions.  It provides a context-sensitive representation that does not map well to OOP but works great with an API.

The approach used here keeps SQL out of your application and provides re-usability by allowing you to store SQL statements with an assigned name and statement grouping.  If the data structure retrieved from datasource requires further munging, it can be managed in the model without removing fine grained control over the SQL execution and optimization. 

###Webservice
The webservice is a django application that is contained in datazilla/webapp/apps/datazilla.  The interface needs to be formalized further. A global datastructure found in datazilla/webapp/apps/datazilla/views.py called, DATAVIEW_ADAPTERS, maps all data views to a data adapter method and set of fields that correspond to signals the data views can send and receive.  This list of signals is passed to the UI as JSON embedded in a hidden input element.  There is a single dataview method that manages traversal of DATAVIEW_ADAPTERS, and provides default behavior for the dataview service. 

```python
DATAVIEW_ADAPTERS = { ##Flat tables SQL##
                      'test_run':{},
                      'test_value':{ 'fields':[ 'test_run_id', ] },
                      'test_option_values':{ 'fields':[ 'test_run_id', ] },
                      'test_aux_data':{ 'fields':[ 'test_run_id', ] },

                      ##API only##
                      'get_test_ref_data':{ 'adapter':_getTestReferenceData},

                      ##Visualization Tools##
                      'test_runs':{ 'adapter':_getTestRunSummary, 'fields':['test_run_id', 'test_run_data'] },

                      'test_chart':{ 'adapter':_getTestRunSummary, 'fields':['test_run_id', 'test_run_data'] },
                      
                      'test_values':{ 'adapter':_getTestValues, 'fields':['test_run_id'] }, 

                      'page_values':{ 'adapter':_getPageValues, 'fields':['test_run_id', 'page_id'] }, 

                      'test_value_summary':{ 'adapter':_getTestValueSummary, 'fields':['test_run_id'] } }
```

The following is an example of a data adapter in the webservice.  Adapters registered in DATAVIEW_ADAPTERS are automatically called with the SQL procedure path, name, and fullpath found in graphs.json assuming the name of the statement matches the key name in DATAVIEW_ADAPTERS.  The keys in DATAVIEW_ADAPTERS correspond to url locations, the example adapter below can be reached at /datazilla/views/api/test_values.

```python
def _getTestValues(procPath, procName, fullProcPath, request, gm):

   data = {};

   if 'test_run_id' in request.GET:
      data = gm.getTestRunValues( request.GET['test_run_id'] )

   jsonData = json.dumps( data )

   return jsonData
```

###UI
The primary component of the UI is the javascript responsible for the data view behavior, located in datazilla/webapp/media/js/data_views.  The HTML associated with a a single data view is described in datazilla/webapp/templates/graphs.views.html, this HTML data view container is cloned for every new data view inserted into the page and added to a single container div with the id dv_view_container.  This provides a single container that components can use to trigger events on, that all dataviews within the page will subscribe to.

All environment information is stored in datazilla/webapp/conf/etc/sysconfig/[datazilla] [3].  Appropriate system information should be added to the environment variables in this file, then copy it to /etc/sysconfig/datazilla or whatever location is appropriate for your environment.  It needs to be source'd before running any component of the system including command line scripts.

The environment variable called DATAZILLA_DEBUG, when set to true, causes all scripts and webservice methods to write out the full SQL, execution time, and host name for any database statement executed.  This is handy for debugging any component in the system.

The web application is a django application found in datazilla/webapp/[apps] [4].  

####Building the Navigation Menu And Defining Data Views
New data views and collections of dataviews can be defined in the navigation menu  by running the command:

```
   python datazilla/webapp/manage.py build_nav
```

This will read the json file datazilla/webapp/templates/data/[views.json] [7].  This structure is translated into the View Navigation menu available on each data view.  It also contains the definitions for the data views.  The following is a definition of a data view in JSON.

```json
   { "name":"test_runs",
     "default_load":1,
     "read_name":"Runs",
     "signals":{ "test_run_id":"1", "test_run_data":"1" },
     "control_panel":"test_selector.html",
     "data_adapter":"test_selector",
     "charts":[ { "name":"average_thumbnails", "read_name":"Averages", "default":"1" }, 
                { "name":"table", "read_name":"Table" } ]
   }
```

Attribute Definitions

```json
   { "name": "Name of the data view",
     "default_load": "If this attribute is present, the data view will try to load data when it initializes",
     "read_name": "Readable name displayed in the UI",
     "signals": "List of signal names that the dataview can send and receive",
     "control_panel": "The html file name to use as the control panel.  Control panel files are located in datazilla/tree/master/webapp/media/html/control_panels",
     "data_adapter": "The data adapter in datazilla/webapp/media/js/data_views/DataAdapterCollection.js",
     "charts": "An array of associative arrays that define what type of visualizations the data view can render"
   }
```


####Building the Cached Summaries


####JS

#####Class Structures
The javascript that implements the user interface is constructed using a page/component/collection pattern thingy... whatever that means.  This pattern was found to be very useful in separating out the required functionality, below is a brief definition of what that means in the data view UI architecture.

######Page
Manages the DOM ready event, implements any top level initialization that's required for the page.  An instance of the page class is the only global variable that other components can access, if they're playing nice.  The page class instance is responsible for instantiating components and storing them in attributes.  The page class also holds any data structures that need to be globally accessible to component classes. 

######Component
Contains the public interface of the component.  A component can encapsulate any functional subset/unit provided in a page.  The component will typically have an instance of a View and Model class.  The component class is also responsible for any required event binding.

######View
A component's view class manages interfacing with the DOM. Any CSS class names or HTML id's are defined as attributes of the view.  Any HTML element modification is controlled with this class.

######Model
A component's model manages any asynchronous data retrieval and large data structure manipulation.

######Collection
A class for managing a collection of Components or classes of any type.  A collection can also have a model/view if appropriate.

######Client Application (datazilla/webapp/media/js/data_views)
This is not a complete file or class listing but is intended to give a top level description of the design pattern thingy of the data view javascript and what the basic functional responsibility of the pages/components/collections are.

#######DataViewPage.js 
DataViewPage Class - Manages the DOM ready event, component initialization, and retrieval of the views.json structure that is used by different components.

#######Bases.js
Design Pattern Base Classes - Contains the base classes for Page, Component, Model, View etc...
                                                                  
#######DataViewComponent.js 
DataViewComponent Class - Encapsulates the behavior of a single data view using a model/view and provides a public interface for data view functionality.  Manages event binding and registration.

DVViewView Class - Encapsulates all DOM interaction required by a data view.

BHViewModel Class - Encapsulates asynchronous server communication and data structure manipulation/retrieval.

#######DataViewCollection.js 

DataViewCollection Class - Manages operations on a collection of data views using a model/view including instantiating view collections.  

DataViewCollectionView Class - Encapsulates all DOM interaction required by the collection.

DataViewCollectionModel Class - Provides an interface to the datastructures holding all data views and their associated parent/child relationships.

#######DataAdapterCollection.js

DataAdapterCollection Class - Collection of DataViewAdapter class instances. 

BHViewAdapter Class - Base class for all BHViewAdapters.  Manages shared view idiosyncratic behavior like what fields go in the control panel and how to populate/retrieve them for signaling behavior.

CrashesAdapter Class - Derived class of BHViewAdapter.  Encapsulates unique behavior for crash data views.

UrlAdapter Class - Derived class of BHViewAdapter. Encapsulates unique behavior for views containing URL summaries.

##Installation
1. Add system info to appropriate files in datazilla/webapp/conf/etc.  Copy the files to there appropriate location under /etc.

2. Start the datazilla, nginx, and memcached services.  There is a startup script for the datazilla and nginx services in datazilla/webapp/conf/bin.

##RHEL6 Configuration

This configuration was done on a RHEL6 VM.

1. cat /etc/redhat-release to get the correct version of EPEL

2. rpm -Uvh http://download.fedora.redhat.com/pub/epel/6/i386/epel-release-6-5.noarch.rpm

3. yum install nginx fcgi Django Django-doc python-docutils MySQL-python python-flup

4. yum install python-setuptools spawn-fcgi

5. yum install mysql.x86_64 mysql-server.x86_64 mysql-devel.x86_64

6. yum install git

7. git clone https://github.com/jeads/datasource, python setup.py install

8. yum install memcached.x86_64 python-memcached.noarch

9. Modify the contents of files in the datazilla/webapp/conf/etc directory to meet the needs of
   your system and then copy the files to their corresponding locations under /etc.


[1]: https://wiki.mozilla.org/Auto-tools/Projects/BugHunter  "bughunter"
[2]: https://wiki.mozilla.org/Buildbot/Talos "Talos"
[3]: https://github.com/jeads/datazilla/blob/master/webapp/conf/etc/sysconfig/datazilla "datazilla"
[4]: https://github.com/jeads/datazilla/tree/master/webapp/apps/ "apps"
[5]: https://github.com/jeads/datasource "datasource"
[6]: https://github.com/jeads/datazilla/blob/master/model/sql/graphs.json "sql"
[7]: https://github.com/jeads/datazilla/blob/master/webapp/templates/data/views.json "views.json"
[8]: https://github.com/jeads/datazilla/tree/master/webapp/media/html/control_panels "control_panels"
[9]: http://seldo.com/weblog/2011/08/11/orm_is_an_antipattern "seldo.com"
