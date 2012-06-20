-- MariaDB dump
--
-- Host: localhost    Database: schema_objectstore_1
-- ------------------------------------------------------
--
-- Table structure for table `objectstore`
--

DROP TABLE IF EXISTS `objectstore`;

CREATE TABLE `objectstore` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT NULL,
  `processed_flag` enum('ready','loading','complete') DEFAULT 'ready',
  `error_flag` enum('N','Y') DEFAULT 'N',
  `error_msg` mediumtext,
  `json_blob` blob,
  `worker_id` int(11),
  PRIMARY KEY (`id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;


-- Dump completed on 2012-06-05 11:02:48
