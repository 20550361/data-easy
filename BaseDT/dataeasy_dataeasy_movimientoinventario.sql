-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: dataeasy
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `dataeasy_movimientoinventario`
--

DROP TABLE IF EXISTS `dataeasy_movimientoinventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataeasy_movimientoinventario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo_movimiento` varchar(10) NOT NULL,
  `cantidad` int unsigned NOT NULL,
  `fecha_movimiento` datetime(6) NOT NULL,
  `producto_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataeasy_movimientoi_producto_id_81fae4e5_fk_dataeasy_` (`producto_id`),
  CONSTRAINT `dataeasy_movimientoi_producto_id_81fae4e5_fk_dataeasy_` FOREIGN KEY (`producto_id`) REFERENCES `dataeasy_producto` (`id`),
  CONSTRAINT `dataeasy_movimientoinventario_chk_1` CHECK ((`cantidad` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataeasy_movimientoinventario`
--

LOCK TABLES `dataeasy_movimientoinventario` WRITE;
/*!40000 ALTER TABLE `dataeasy_movimientoinventario` DISABLE KEYS */;
INSERT INTO `dataeasy_movimientoinventario` VALUES (1,'entrada',150,'2025-11-16 03:35:08.013552',1),(2,'entrada',25,'2025-11-16 03:35:08.040994',2),(3,'entrada',75,'2025-11-16 03:35:08.075579',3),(4,'entrada',150,'2025-11-16 03:35:08.108996',4),(5,'entrada',60,'2025-11-16 03:35:08.140182',5),(6,'entrada',40,'2025-11-16 03:35:08.155609',6),(7,'entrada',15,'2025-11-16 03:35:08.186146',7),(8,'entrada',120,'2025-11-16 03:35:08.212878',8),(9,'entrada',8,'2025-11-16 03:35:08.228299',9),(10,'entrada',500,'2025-11-16 03:35:08.260075',10);
/*!40000 ALTER TABLE `dataeasy_movimientoinventario` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-16  1:12:49
