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
);

CREATE TABLE `method` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin NOT NULL,
  `code_ref` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
);

CREATE TABLE `metric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
);

CREATE TABLE `operating_system` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_bin NOT NULL,
  `version` varchar(50) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_os` (`name`,`version`)
);

CREATE TABLE `option` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_option` (`name`)
);

CREATE TABLE `test` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  `version` int(11) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `aux_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `name` varchar(25) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `test_id_key` (`test_id`),
  CONSTRAINT `fk_aux_data_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
);

CREATE TABLE `pages` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `url` varchar(1000) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_id_key` (`test_id`),
  CONSTRAINT `fk_pages_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
);

CREATE TABLE `product` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product` varchar(50) COLLATE utf8_bin NOT NULL,
  `branch` varchar(128) COLLATE utf8_bin DEFAULT NULL,
  `version` varchar(16) COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_branch` (`product`,`branch`,`version`)
);

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
);

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
);

CREATE TABLE `test_collection` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8_bin NOT NULL,
  `description` mediumtext COLLATE utf8_bin,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
);

CREATE TABLE `test_collection_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) DEFAULT NULL,
  `test_collection_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `operating_system_id` varchar(45) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_test_collection_map_test_collection` (`test_collection_id`),
  CONSTRAINT `fk_test_collection_map_test_collection` FOREIGN KEY (`test_collection_id`) REFERENCES `test_collection` (`id`)
);

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
);

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
);

CREATE TABLE `test_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_run_id` int(11) NOT NULL,
  `data` mediumtext COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_id_key` (`test_run_id`),
  CONSTRAINT `fk_test_data_test_run` FOREIGN KEY (`test_run_id`) REFERENCES `test_run` (`id`)
);

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
);

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
);

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
);

CREATE TABLE `value` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(25) NOT NULL,
  `description` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
);

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
);
