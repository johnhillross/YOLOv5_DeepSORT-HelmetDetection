/*
 Navicat Premium Data Transfer

 Source Server         : MySQL
 Source Server Type    : MySQL
 Source Server Version : 50733
 Source Host           : localhost:3306
 Source Schema         : eb_helmet

 Target Server Type    : MySQL
 Target Server Version : 50733
 File Encoding         : 65001

 Date: 24/05/2021 21:10:23
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for eb_rider
-- ----------------------------
DROP TABLE IF EXISTS `eb_rider`;
CREATE TABLE `eb_rider`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `identitie` int(11) NOT NULL,
  `lane` tinyint(4) NOT NULL,
  `direction` tinyint(4) NOT NULL,
  `helmet` tinyint(4) NOT NULL,
  `path` varchar(50) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `time` datetime(0) NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = latin1 COLLATE = latin1_swedish_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for webcam
-- ----------------------------
DROP TABLE IF EXISTS `webcam`;
CREATE TABLE `webcam`  (
  `device` varchar(10) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `longitude` float(9, 6) NOT NULL,
  `latitude` float(9, 6) NOT NULL,
  `source` varchar(100) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  PRIMARY KEY (`device`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = latin1 COLLATE = latin1_swedish_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
