-- MySQL dump 10.13  Distrib 5.1.61, for redhat-linux-gnu (x86_64)
--
-- Host: localhost    Database: schema_1_perftest
-- ------------------------------------------------------
-- Server version	5.1.61

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `aux_data`
--

DROP TABLE IF EXISTS `aux_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/***********
aux_data - Description

The aux in aux_data stands for auxiliary.  Auxiliary 
data can be any type of meta-data associated with a test.  
Some examples of auxiliary data would be RAM or cpu 
consumption over the life cycle of a test.  This table 
would hold them name and description of different types of 
auxiliary data, while test_aux_data holds the auxiliary 
data values generated.
************/
CREATE TABLE `aux_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `test_id_key` (`test_id`),
  CONSTRAINT `fk_aux_data_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `build`
--

DROP TABLE IF EXISTS `build`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/**************
build - Description

This table stores product builds associated with test 
runs.  It maps the build to the operating system, product, 
and machine.  Test runs can share a build or use different 
builds.
****************/
CREATE TABLE `build` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operating_system_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `machine_id` int(11) NOT NULL,
  `test_build_id` varchar(16) NOT NULL,
  `processor` varchar(25) NOT NULL,
  `revision` varchar(16) NOT NULL,
  `build_type` varchar(25) NOT NULL,
  `build_date` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `machine_id_key` (`machine_id`),
  KEY `build_type_key` (`build_type`),
  KEY `build_date_key` (`build_date`),
  KEY `operating_system_id_key` (`operating_system_id`),
  KEY `changeset_key` (`revision`),
  KEY `fk_build_product` (`product_id`),
  CONSTRAINT `fk_build_machine` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`),
  CONSTRAINT `fk_build_operating_system` FOREIGN KEY (`operating_system_id`) REFERENCES `operating_system` (`id`),
  CONSTRAINT `fk_build_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `machine`
--

DROP TABLE IF EXISTS `machine`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/****************
machine - Description

This table contains a unique list of machine names.  
A machine is associated with every build and test run.  
This can be used for examining any trends in the test 
data that seem to be machine or environment specific.
*****************/
CREATE TABLE `machine` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `is_throttling` tinyint(3) NOT NULL DEFAULT '0',
  `cpu_speed` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `name` varchar(255) COLLATE utf8_bin NOT NULL,
  `is_active` tinyint(3) NOT NULL DEFAULT '0',
  `date_added` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `unique_machine` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `method`
--

DROP TABLE IF EXISTS `method`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/***************
method - Description

The method associated with a metric that is associated 
with a particular test run.  A possible example of this 
might be a particular method for calculating whether a 
performance regression has occurred on a test run.  The 
code_ref column would store a reference to the actual 
implementation of the method.
****************/
CREATE TABLE `method` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin NOT NULL,
  `code_ref` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metric`
--

DROP TABLE IF EXISTS `metric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/*************
metric - Description

The metric table contains a list of metrics that can 
be used to calculate values in test_metric.  So a metric 
can have different methods associated with it and can also 
be associated with any number of test values.  A metric 
could be any type of calculation such as standard deviation,
 a t-test, or p-value etc...
**************/
CREATE TABLE `metric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `operating_system`
--

DROP TABLE IF EXISTS `operating_system`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/*************
operating_system - Description

This table contains a unique list of operating systems that 
tests are run on.
**************/
CREATE TABLE `operating_system` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_bin NOT NULL,
  `version` varchar(50) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_os` (`name`,`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `option`
--

DROP TABLE IF EXISTS `option`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/***************
option - Description

The options table contains a unique list of options 
associated with a particular test run.  These options 
could be command line options to the program running 
the test, or any other type of option that dictates 
how a particular test is run or behaves.
*****************/
CREATE TABLE `option` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_option` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pages`
--

DROP TABLE IF EXISTS `pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/**************
pages - Description

This table contains a complete listing of all of the pages 
associated with all of the tests.  Every test value has a page 
associated with it.
***************/
CREATE TABLE `pages` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `url` varchar(1000) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_id_key` (`test_id`),
  CONSTRAINT `fk_pages_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/***************
product - Description

This table contains the list of products and their associated 
branches and versions.  Each unique combination of a product, 
branch, and version receive's a new id and is referred to as 
the product_id in other tables.
****************/
CREATE TABLE `product` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product` varchar(50) COLLATE utf8_bin NOT NULL,
  `branch` varchar(128) COLLATE utf8_bin DEFAULT NULL,
  `version` varchar(16) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_branch` (`product`,`branch`,`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `summary_cache`
--

DROP TABLE IF EXISTS `summary_cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/****************
summary_cache - Description

The summary cache table holds JSON blobs that need to be 
stored in a  persistent cache.  These blobs are added to 
a memcache and used by the user interface to reduce load 
on the database and improve performance for the user.  
Currently this includes a 7 and 30 day summary of all test runs.  
The columns item_id and item_data allow for the construction of 
a two part key for a key value object store.
*****************/
CREATE TABLE `summary_cache` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `item_data` varchar(128) COLLATE utf8_bin DEFAULT NULL,
  `value` mediumtext COLLATE utf8_bin NOT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id_item_data` (`item_id`,`item_data`),
  KEY `item_id_key` (`item_id`),
  KEY `item_data_key` (`item_data`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test`
--

DROP TABLE IF EXISTS `test`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/****************
test - Description

The test table stores the complete list of test names and 
their associated descriptions.  A test can also be versioned.  
For a talos test, a new version might be created when the set 
of pages associated with a test is modified.  All test runs 
have a test_id associated with them.
*****************/
CREATE TABLE `test` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  `version` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_aux_data`
--

DROP TABLE IF EXISTS `test_aux_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/****************
test_aux_data - Description

This table stores auxiliary data associated with test runs.  
The associated data can be either numeric or string based.
*****************/
CREATE TABLE `test_aux_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_run_id` int(11) NOT NULL,
  `run_id` int(11) NOT NULL,
  `aux_data_id` int(11) NOT NULL,
  `numeric_data` double DEFAULT NULL,
  `string_data` varchar(50) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_id_key` (`test_run_id`),
  KEY `fk_aux_data` (`aux_data_id`),
  CONSTRAINT `fk_test_aux_data_test_run` FOREIGN KEY (`test_run_id`) REFERENCES `test_run` (`id`),
  CONSTRAINT `fk_aux_data` FOREIGN KEY (`aux_data_id`) REFERENCES `aux_data` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_collection`
--

DROP TABLE IF EXISTS `test_collection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/******************
test_collection - Description

The test collection table holds a collection of tests 
that are examined as a group in the user interface.  
The test collections can be accessed on the control 
menu of "Runs" data view which holds a summary of all 
test runs.
********************/
CREATE TABLE `test_collection` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_collection_map`
--

DROP TABLE IF EXISTS `test_collection_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/*******************
test_collection_map - Description

This table holds a mapping of test_id, operating_system_id, 
and product_id for a given test collection.  This allows the 
user interface to provide pre-defined test/platform combinations 
for users to examine using any combination of those three id types.
*********************/
CREATE TABLE `test_collection_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) DEFAULT NULL,
  `test_collection_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `operating_system_id` varchar(45) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_test_collection_map_test_collection` (`test_collection_id`),
  CONSTRAINT `fk_test_collection_map_test_collection` FOREIGN KEY (`test_collection_id`) REFERENCES `test_collection` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_data`
--

DROP TABLE IF EXISTS `test_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/******************
test_data - Description

Test data holds the JSON blob submitted by the worker bot that 
runs the tests.  This table is essentially a key/value object 
store and should really not be in the RDBS but should be placed 
in an object store.  The JSON structures stored here are expanded 
into the rest of the schema.
******************/
CREATE TABLE `test_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_run_id` int(11) NOT NULL,
  `data` mediumtext COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_id_key` (`test_run_id`),
  CONSTRAINT `fk_test_data_test_run` FOREIGN KEY (`test_run_id`) REFERENCES `test_run` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_metric`
--

DROP TABLE IF EXISTS `test_metric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/*************
test_metric - Description

The test_metric table contains metrics associated with a 
test run.  A metric could be any type of calculation 
such as standard deviation, a t-test, or p-value etc...
**************/
CREATE TABLE `test_metric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_run_id` int(11) NOT NULL,
  `method_id` int(11) NOT NULL,
  `metric_id` int(11) NOT NULL,
  `value` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_id_key` (`test_run_id`),
  KEY `method_id_key` (`method_id`),
  KEY `metric_id_key` (`metric_id`),
  CONSTRAINT `fk_test_metric_method` FOREIGN KEY (`method_id`) REFERENCES `method` (`id`),
  CONSTRAINT `fk_test_metric_metric` FOREIGN KEY (`metric_id`) REFERENCES `metric` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_option_values`
--

DROP TABLE IF EXISTS `test_option_values`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/***************
test_option_values - Description

This table contains options associated with a particular 
test run.  These options could be command line options to 
the program running the test, or any other type of option 
that dictates how a particular test is run or behaves.
****************/
CREATE TABLE `test_option_values` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_run_id` int(11) NOT NULL,
  `option_id` int(11) NOT NULL,
  `value` varchar(25) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_id_key` (`test_run_id`),
  KEY `option_id_key` (`option_id`),
  CONSTRAINT `fk_test_option_values_option` FOREIGN KEY (`option_id`) REFERENCES `option` (`id`),
  CONSTRAINT `fk_test_option_values_test_run` FOREIGN KEY (`test_run_id`) REFERENCES `test_run` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_run`
--

DROP TABLE IF EXISTS `test_run`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/****************
test_run - Description

The test run is associated with a particular revision (this 
corresponds to changeset in mercurial).  Each test run has 
a single test associated with it.  It will also have a build 
associated with it but the same build could be associated with 
multiple test runs.
*****************/
CREATE TABLE `test_run` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `build_id` int(11) NOT NULL,
  `revision` varchar(16) NOT NULL,
  `date_run` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_id_key` (`test_id`),
  KEY `build_id_key` (`build_id`),
  KEY `date_run_key` (`date_run`),
  KEY `changeset_key` (`revision`),
  CONSTRAINT `fk_test_run_build` FOREIGN KEY (`build_id`) REFERENCES `build` (`id`),
  CONSTRAINT `fk_test_run_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_value`
--

DROP TABLE IF EXISTS `test_value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/********************
test_value - Description

This table holds the raw data for each replicate.  The 
run_id column is a unique identifier used to distinguish multiple 
replicates for the same page_id.  A test can have one or more 
replicates.
*********************/
CREATE TABLE `test_value` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_run_id` int(11) NOT NULL,
  `run_id` int(11) NOT NULL,
  `page_id` int(11) DEFAULT NULL,
  `value_id` int(11) NOT NULL,
  `value` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_id_key` (`test_run_id`),
  KEY `page_id_key` (`page_id`),
  CONSTRAINT `fk_test_value_test_run` FOREIGN KEY (`test_run_id`) REFERENCES `test_run` (`id`),
  CONSTRAINT `fk_test_value_page` FOREIGN KEY (`page_id`) REFERENCES `pages` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `threshold`
--

DROP TABLE IF EXISTS `threshold`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/*********************
threshold - Description

The threshold table is intended to associate a threshold value 
with a particular test and value type combination.  When this 
threshold is surpassed the test is considered to be a failure.
**********************/
CREATE TABLE `threshold` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `value_id` int(11) NOT NULL,
  `test_id` int(11) NOT NULL,
  `standard` double NOT NULL,
  `creation_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `value_id_key` (`value_id`),
  KEY `creation_date_key` (`creation_date`),
  KEY `test_id_key` (`test_id`),
  CONSTRAINT `fk_threshold_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`),
  CONSTRAINT `fk_threshold_value` FOREIGN KEY (`value_id`) REFERENCES `value` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `value`
--

DROP TABLE IF EXISTS `value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;

/*********************
value - Description

This table contains a unique list of value types that are 
stored in the test_value and are associated with each test run.  
The most common value type is run_time and describes the time 
it took for a particular product to load a page.
**********************/
CREATE TABLE `value` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) NOT NULL,
  `description` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-05-01 11:02:48
