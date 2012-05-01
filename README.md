#Datazilla
Datazilla is a system for managing and visualizing data.  The fundamental unit of data display in the user interface is called a data view.  Data views can display data in any number of ways: tabular or graphical.  Data views can also send signals to one another enabling the user to maintain visual context across multiple graphical displays of different data types.  Each data view shares a toolbar that abstracts navigation, data presentation controls, and visual presentation.  A prototype of datazilla was first developed in an application called [bughunter] [1].

This project includes a model, web service, and web based user interface, and eventually it will support a local development environment. 

This is a work in progress and will likely see a number of structural changes.  It is currently being developed to manage [Talos] [2] test data, a performance testing framework developed by mozilla for testing software products.

##Architecture
At a top level datazilla consists of three components: [Model](https://github.com/jeads/datazilla#model), [Web Service](https://github.com/jeads/datazilla#web-service), [User Interface](https://github.com/jeads/datazilla#user-interface), and [Data Model](https://github.com/jeads/datazilla#data-model).

###Model
The model layer found in [/datazilla/model](https://github.com/jeads/datazilla/tree/master/model) provides an interface for getting/setting data in a database.  The datazilla model classes rely on a module called [datasource] [5].  This module encapsulates SQL manipulation.  All of the SQL used by the system is stored in a JSON file found in [/datazilla/model/sql](https://github.com/jeads/datazilla/blob/master/model/sql/graphs.json).  There can be any number of SQL files stored in this format.  The JSON structure allows SQL to be stored in named associative arrays that also contain the host type to be associated with each statement.  Any command line script or web service method that requires data should use a derived model class to obtain it.

```python
gm = DatazillaModel('graphs.json')
products = gm.getProductTestOsMap()
```

The ```gm.getProductTestOsMap()``` method looks like
```python
   def getProductTestOsMap(self):

      productTuple = self.dhub.execute(proc='graphs.selects.get_product_test_os_map',
                                       debug_show=self.DEBUG,
                                       return_type='tuple') 

      return productTuple
```

```graphs.selects.get_product_test_os_map``` found in [datazilla/model/sql/graphs.json](https://github.com/jeads/datazilla/blob/master/model/sql/graphs.json) looks like
```json
{
   "selects":{  

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
      
      "...more SQL statements..."
}
```
The string, ```graphs```, in ```graphs.selects.get_product_test_os_map``` refers to the SQL file name to load in [/datazilla/model/sql](https://github.com/jeads/datazilla/tree/master/model/sql).  The SQL in graphs.json can also be written with placeholders and a string replacement system, see [datasource] [5] for all of the features available.

If you're thinking why not just use an ORM?  I direct you to [seldo.com] [9] where you will find a most excellent answer to your question that I completely agree with.  It has been my experience that ORMs don't scale well with data models that need to scale horizontally.  They also fail to represent relational data accurately in OOP like objects.  If you can represent your data model with objects, then use an object store not an RDBS.  SQL answers questions.  It provides a context-sensitive representation that does not map well to OOP but works great with an API.

The approach used here keeps SQL out of your application and provides re-usability by allowing you to store SQL statements with an assigned name and statement grouping.  If the data structure retrieved from datasource requires further munging, it can be managed in the model without removing fine grained control over the SQL execution and optimization. 

###Web Service
The web service is a django application, found in [/datazilla/webapp/apps/datazilla](https://github.com/jeads/datazilla/tree/master/webapp/apps).  The interface needs to be formalized further. A global datastructure, found in [/datazilla/webapp/apps/datazilla/views.py](https://github.com/jeads/datazilla/blob/master/webapp/apps/datazilla/views.py) called, ```DATAVIEW_ADAPTERS```, maps all data views to a data adapter method and set of fields that correspond to signals the data views can send and receive.  This list of signals is passed to the UI as JSON embedded in a hidden input element.  There is a single data view method that manages traversal of ```DATAVIEW_ADAPTERS```, and provides default behavior for the data view service. 

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

The following is an example of a data adapter in the web service.  Adapters registered in ```DATAVIEW_ADAPTERS``` are automatically called with the SQL procedure path, name, and fullpath found in graphs.json assuming the name of the statement matches the key name in ```DATAVIEW_ADAPTERS```.  The keys in ```DATAVIEW_ADAPTERS``` correspond to url locations, the example adapter below can be reached at /datazilla/views/api/test_values.

```python
def _getTestValues(procPath, procName, fullProcPath, request, gm):

   data = {};

   if 'test_run_id' in request.GET:
      data = gm.getTestRunValues( request.GET['test_run_id'] )

   jsonData = json.dumps( data )

   return jsonData
```

All environment variables required by datazilla are stored in a single file located in [/datazilla/webapp/conf/etc/sysconfig](https://github.com/jeads/datazilla/blob/master/webapp/conf/etc/sysconfig/). There is a single environment variable, ```DATAZILLA_DEBUG```, that can be used to turn on debugging options across all command line scripts and the django web service.  When set, the following message will be written to the server log or to stdout, if executing a command line script whenever SQL is executed in the application.

```
datasource.hubs.MySQL.MySQL debug message:
   host:hostname.somewhere.com db:db_name host_type:master_host proc:graphs.selects.get_test_run_summary
   Executing SQL:SELECT tr.id AS 'test_run_id', tr.revision, tr.date_run, b.product_id, tr.test_id, b.operating_system_id, ROUND( AVG(tv.value), 2 ) AS average, ROUND( MIN(tv.value), 2 ) AS min, ROUND( MAX(tv.value), 2 ) AS max, ROUND( STDDEV(tv.value), 2 ) AS 'standard_deviation', ROUND( VARIANCE(tv.value), 2 ) AS variance FROM test_run AS tr LEFT JOIN test_value AS tv ON tr.id = tv.test_run_id LEFT JOIN build AS b ON tr.build_id = b.id WHERE (tr.date_run >= '1334855411' AND tr.date_run <= '1335460211') AND b.product_id IN (46) GROUP BY tr.id, tr.revision, b.product_id, tr.test_id, b.operating_system_id ORDER BY tr.date_run, tr.test_id ASC
   Execution Time:4.1700e-01 sec
```

####Building the Navigation Menu And Defining Data Views
New data views and collections of dataviews can be defined in the navigation menu  by running the command:

```
   python datazilla/webapp/manage.py build_nav
```

This will read the json file [/datazilla/webapp/templates/data/views.json](https://github.com/jeads/datazilla/blob/master/webapp/templates/data/views.json) and generate two files from it: [nav_menu.html](https://github.com/jeads/datazilla/blob/master/webapp/media/html/nav_menu.html) and [graphs.navlookup.html](https://github.com/jeads/datazilla/blob/master/webapp/templates/graphs.navlookup.html). 

A sample dataview from [views.json](https://github.com/jeads/datazilla/blob/master/webapp/templates/data/views.json) is shown below:

```json
   { "name":"test_runs",
     "default_load":"1",
     "read_name":"Runs",
     "signals":{ "test_run_id":"1", "test_run_data":"1" },
     "control_panel":"test_selector.html",
     "data_adapter":"test_selector",
     "charts":[ { "name":"average_thumbnails", "read_name":"Averages", "default":"1" }, 
                { "name":"table", "read_name":"Table" } ]
   }
```

The attributes in this JSON structure are defined below:

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
[nav_menu.html](https://github.com/jeads/datazilla/blob/master/webapp/media/html/nav_menu.html) contains a ```<ul>lots of stuff</ul>``` that all data views use for a navigation menu.

[graphs.navlookup.html](https://github.com/jeads/datazilla/blob/master/webapp/templates/graphs.navlookup.html) contains an HTML element ```<input type="hidden">JSON Associative Array</input>``` that is deserialized into an associative array where the keys are all of the unique data view names and the values are the data view objects found in [/datazilla/webapp/templates/data/views.json](https://github.com/jeads/datazilla/blob/master/webapp/templates/data/views.json).  This gives access to the data view configurations in the javascript environment.  It is used to configure the user interface, to reduce server calls it's embedded in the page when it loads.

####Building the Cached Summaries
The test run data is cached in JSON structures for every platform and test combination for 7 day and 30 day time periods.  An example datastructure is depicted below:

```json
{
    "data": [
        {
            "date_run": "1334863012",
            "product_id": "18",
            "operating_system_id": "27",
            "min": "2084.49",
            "max": "8478.53",
            "average": "3830.88",
            "test_run_id": "56455",
            "standard_deviation": "2122.99",
            "variance": "4507101.82",
            "test_id": "12",
            "revision": "ac3ea3b31fe0"
        },
        {
            "date_run": "1334863012",
            "product_id": "18",
            "operating_system_id": "27",
            "min": "86.83",
            "max": "205.52",
            "average": "132.76",
            "test_run_id": "56450",
            "standard_deviation": "42.91",
            "variance": "1841.13",
            "test_id": "20",
            "revision": "ac3ea3b31fe0"
        },
        
        "...lots more data objects..."
        
   ],
    "columns": [
        "test_run_id",
        "revision",
        "date_run",
        "product_id",
        "test_id",
        "operating_system_id",
        "average",
        "min",
        "max",
        "standard_deviation",
        "variance"
    ]
}
```

This data structure is currently stored in a table in the database, this will probably get moved to a key/value object store like HBase as this project progresses.  It needs to persist if memcached is rebooted.  It currently takes several minutes to generate all of the combinatorial possiblities, this generation time will begin to take longer as the data grows.  To build and cache this data use [/datazilla/controller/admin/populate_summary_cache.py](https://github.com/jeads/datazilla/blob/master/controller/admin/populate_summary_cache.py).

To build the json structures and store them in the database, run:
```
python /datazilla/controller/admin/populate_summary_cache.py --build
```

To cache the structures in memcached, run:
```
python /datazilla/controller/admin/populate_summary_cache.py --cache
```

###User Interface
The javascript responsible for the data view behavior is located in [/datazilla/webapp/media/js/data_views](https://github.com/jeads/datazilla/tree/master/webapp/media/js/data_views).  The HTML associated with a single data view is described in [/datazilla/webapp/templates/graphs.views.html](https://github.com/jeads/datazilla/blob/master/webapp/templates/graphs.views.html).  

This HTML data view container is cloned for every new data view inserted into the page.  It's added to a single container ```div``` with the id ```dv_view_container```.  This provides a single container that components can use to trigger events on, that all data views within the page will subscribe to.

####Javascript Design Patterns And Class Structures
The javascript that implements the user interface is constructed using a page/component/collection pattern thingy... whatever that means.  Seriously though, the pattern was found to be very useful in separating out the required functionality.  A description of how it all works is provided below.  The goal was to isolate the parts of a data view that are unique and provide a straight forward way for a developer to modify the content displayed for a data view without having to deal with any of the core data view code in [DataViewComponent.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataViewComponent.js) or [DataViewCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataViewCollection.js).
The two modules that are relevant for extending the javascript with a new visualization or control for a data view are: [DataAdapterCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataAdapterCollection.js) and [VisualizationCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/VisualizationCollection.js).

[DataAdapterCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataAdapterCollection.js) provides an interface to write a custom adapter for data coming into a data view and also provide custom processing for the control panel associated with a data view.

[VisualizationCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/VisualizationCollection.js) provides a collection of visualization adapters that can be associated with any data view.

The interface for accomplishing these tasks needs to be solidified and then a straightforward way of adding a new class that extends both collections added.  The collections provided in the existing classes will provide a set of stock control panels and visualizations to use.  If a developer wants to add new content to a data view that requires a new control panel or visualization they should be able to do this by adding a new javascript file with appropriate collection extensions.  This interface needs to be developed a bit further to get to this point.

#####Page
Manages the DOM ready event, implements any top level initialization that's required for the page.  An instance of the page class is the only global variable that other components can access, if they're playing nice.  The page class instance is responsible for instantiating components and storing them in attributes.  The page class also holds any data structures that need to be globally accessible to component classes. 

#####Component
Contains the public interface of the component.  A component can encapsulate any functional subset/unit provided in a page.  The component will typically have an instance of a View and Model class.  The component class is also responsible for any required event binding.

#####View
A component's view class manages interfacing with the DOM. Any CSS class names or HTML id's are defined as attributes of the view.  Any HTML element modification is controlled with this class.

#####Model
A component's model manages any asynchronous data retrieval and large data structure manipulation.

#####Collection
A class for managing a collection of Components or classes of any type.  A collection can also have a model/view if appropriate.

#####Client Application 

All of the client application javascript for data views is contained in [datazilla/webapp/media/js/data_views](https://github.com/jeads/datazilla/tree/master/webapp/media/js/data_views).
This is not a complete file or class listing but is intended to give a top level description of the design pattern thingy of the data view javascript and what the basic functional responsibility of the pages/components/collections are.

######[Bases.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/Bases.js)
Contains the base classes for Page, Component, Model, View etc...

######[DataViewPage.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataViewPage.js) 
```DataViewPage``` A class that manages the DOM ready event, component initialization, and retrieval of the views.json structure that is used by different components.

######[DataViewComponent.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataViewComponent.js)
```DataViewComponent``` Class that encapsulates the behavior of a single data view using a model/view and provides a public interface for data view functionality.  Manages event binding and registration.

```DataViewView``` Class that encapsulates all DOM interaction required by a data view.

```DataViewModel``` Class that encapsulates asynchronous server communication and data structure manipulation/retrieval.

######[DataViewCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataViewCollection.js)

```DataViewCollection``` Class that manages operations on a collection of data views using a model/view including instantiating view collections.  

```DataViewCollectionView``` Class that encapsulates all DOM interaction required by the collection.

```DataViewCollectionModel``` Class that provides an interface to the datastructures holding all data views and their associated parent/child relationships.

######[DataAdapterCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/DataAdapterCollection.js)

```DataAdapterCollection``` Class provides a collection of DataViewAdapter class instances. 

```DataViewAdapter``` A Base class for all DataViewAdapters.  Manages shared view idiosyncratic behavior like what fields go in the control panel and how to populate/retrieve them for signaling behavior.

######[VisualizationCollection.js](https://github.com/jeads/datazilla/blob/master/webapp/media/js/data_views/VisualizationCollection.js)

```VisualizationCollection``` Class provides a collection of Visualization class instances.

```Visualization``` Base class for derived visualization classes.

###Data Model

The data model for performance data consists of a RDBS [schema](https://github.com/jeads/datazilla/blob/master/model/sql/template_schema/schema_1_perftest.sql), an image of the schema is available in [schema_1_perftest.png](https://github.com/jeads/datazilla/blob/master/model/sql/template_schema/schema_1_perftest.png) that is useful for understanding the relationships in the data model.  

Data is deposited using a JSON structure, an example input structure can be found [here](https://github.com/jeads/datazilla/blob/master/model/sql/template_schema/schema_1_perftest.json).

The follow excerpt shows sections of the JSON structure and where the JSON attributes end up in the schema.  Reference data such as option names, product names, os names etc... Are dynamically loaded into the reference data section of the schema when a new data type is detected, if the reference data has already been seen before the appropriate id column value is associated with the data.

```
                                                   schema_1_perftest.table.column
    "test_build": {                                ------------------------------
        "branch": "",                              product.branch
        "id": "20120228122102",                    build.test_build_id
        "name": "Firefox",                         product.name
        "revision": "785345035a3b",                test_run.revision & build.revision
        "version": "13.0a1"                        product.version
    }, 
    "test_machine": {   
        "name": "qm-pxp01",                        machine.name
        "os": "linux",                             operating_system.name
        "osversion": "Ubuntu 11.10",               operating_system.version
        "platform": "x86_64"                       build.processor
    }, 
    "testrun": {
        "date": "1330454755",                      test_run.date_run
        "options": {                         
            "responsiveness": "false",             option.name=responsiveness    test_option_values.value="false"
            "rss": "true",                         option.name=rss               test_option_values.value="true"
            "shutdown": "true",                    option.name=shutdown          test_option_values.value="true"
            "tpchrome": "true",                    option.name=tpchrome          test_option_values.value="true"
            "tpcycles": "3",                       option.name=tpcycles          test_option_values.value="3"
            "tpdelay": "",                         option.name=tpdelay           test_option_values.value=""
            "tpmozafterpaint": "false",            option.name=tpmozafterpaint   test_option_values.value="false"
            "tppagecycles": "1",                   option.name=tppagecycles      test_option_values.value="1"
            "tprender": "false"                    option.name=tprender          test_option_values.value="false"
        }, 
        "suite": "Talos tp5r"                      test.name
    }

```
The following JSON to schema mapping shows where the raw data ends up.

```
                                                   schema_1_perftest.table.column
    "results": {                                   ------------------------------
        "163.com": [                               page.name
            "666.0",                               test_value.value=666.0  test_value.run_id=0
            "587.0",                               test_value.value=587.0  test_value.run_id=1
            "626.0"                                test_value.value=626.0  test_value.run_id=2
        ], 
        "56.com": [                                page.name
            "789.0",                               test_value.value=789.0  test_value.run_id=0
            "705.0",                               test_value.value=705.0  test_value.run_id=1
            "739.0"                                test_value.value=739.0  test_value.run_id=2
        ], 
        "alibaba.com": [                           page.name
            "103.0",                               test_value.value=103.0  test_value.run_id=0
            "95.0",                                test_value.value=95.0   test_value.run_id=1
            "105.0"                                test_value.value=105.0  test_value.run_id=2
        ], 

    ...lots more data...

    "results_aux": {
        "main_rss": [                              aux_data.name=main_rss
            "72122368",                            test_aux_data.numeric_data                         
            "89206784",                            test_aux_data.numeric_data
            "90710016",                            test_aux_data.numeric_data
            "93384704",                            test_aux_data.numeric_data
            "98676736",                            test_aux_data.numeric_data
            "102776832",                           test_aux_data.numeric_data
            "104378368",                           test_aux_data.numeric_data

    ...lots more data...
```

##Installation
1. Add system info to appropriate files in datazilla/webapp/conf/etc.  Copy the files to there appropriate location under /etc.

2. Start the datazilla, nginx, and memcached services.  There is a startup script for the datazilla and nginx services in datazilla/webapp/conf/bin.

##RHEL6 Configuration

This configuration was done on a RHEL6 VM.

1. cat /etc/redhat-release to get the correct version of EPEL

2. rpm -Uvh http://download.fedora.redhat.com/pub/epel/6/i386/epel-release-6-5.noarch.rpm

3. yum install nginx fcgi python-docutils MySQL-python python-flup

4. yum install python-setuptools spawn-fcgi

5. yum install mysql.x86_64 mysql-server.x86_64 mysql-devel.x86_64

6. yum install git

7. yum install memcached.x86_64 python-memcached.noarch

8. Download the most recent version of [django] [10] and install it.  If there is already a version of django installed on your system, make sure it's 1.3.1 or later.  If not make sure to completely delete the pre-existing django version from your system before installing the new one.

9. git clone https://github.com/jeads/datasource, python setup.py install

10. Modify the contents of files in the datazilla/webapp/conf/etc directory to meet the needs of
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
[10]: https://www.djangoproject.com/ "django"
