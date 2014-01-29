/*****
Set of SQL schema modifications to support b2g like data. To implement,
change the project string to the target project name and execute the sql.
******/
SET foreign_key_checks = 0;

DROP TABLE `project_perftest_1`.`test_run`;

CREATE TABLE `project_perftest_1`.`test_run` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `build_id` int(11) NOT NULL,
  `machine_id` int(11) NOT NULL,
  `revision` varchar(50) DEFAULT NULL,
  `date_run` int(11) NOT NULL,
  `status` tinyint(4) NOT NULL DEFAULT '1',
  `gecko_revision` varchar(50) DEFAULT NULL,
  `build_revision` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_id_key` (`test_id`),
  KEY `build_id_key` (`build_id`),
  KEY `machine_id_key` (`machine_id`),
  KEY `date_run_key` (`date_run`),
  KEY `changeset_key` (`revision`),
  KEY `status_key` (`status`),
  KEY `gecko_revision_key` (`gecko_revision`),
  KEY `build_revision_key` (`build_revision`),
  CONSTRAINT `fk_test_run_build` FOREIGN KEY (`build_id`) REFERENCES `build` (`id`),
  CONSTRAINT `fk_test_run_machine` FOREIGN KEY (`machine_id`) REFERENCES `machine` (`id`),
  CONSTRAINT `fk_test_run_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE `project_perftest_1`.`machine`;

CREATE TABLE `project_perftest_1`.`machine` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `is_throttling` tinyint(3) NOT NULL DEFAULT '0',
  `cpu_speed` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `name` varchar(255) COLLATE utf8_bin NOT NULL,
  `type` varchar(50) COLLATE utf8_bin DEFAULT NULL,
  `operating_system_id` int(11) NOT NULL,
  `is_active` tinyint(3) NOT NULL DEFAULT '0',
  `date_added` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_machine` (`name`,`operating_system_id`),
  KEY `operating_system_id_key` (`operating_system_id`),
  CONSTRAINT `fk_machine_operating_system` FOREIGN KEY (`operating_system_id`) REFERENCES `operating_system` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE `project_perftest_1`.`build` MODIFY `revision` varchar (50);
ALTER TABLE `project_perftest_1`.`test_run` MODIFY `revision` varchar (50);
ALTER TABLE `project_perftest_1`.`metric_threshold` MODIFY `revision` varchar (50);
ALTER TABLE `project_perftest_1`.`test_data_all_dimensions` MODIFY `revision` varchar (50);
ALTER TABLE `project_perftest_1`.`application_log` MODIFY `revision` varchar (50);

SET foreign_key_checks = 1;
