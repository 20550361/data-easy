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
-- Table structure for table `dataeasy_producto`
--

DROP TABLE IF EXISTS `dataeasy_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataeasy_producto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre_producto` varchar(100) NOT NULL,
  `descripcion` longtext,
  `stock_actual` int NOT NULL,
  `stock_minimo` int NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `categoria_id` bigint DEFAULT NULL,
  `marca_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre_producto` (`nombre_producto`),
  KEY `dataeasy_producto_categoria_id_3e0b010c_fk_dataeasy_categoria_id` (`categoria_id`),
  KEY `dataeasy_producto_marca_id_325581b3_fk_dataeasy_marca_id` (`marca_id`),
  CONSTRAINT `dataeasy_producto_categoria_id_3e0b010c_fk_dataeasy_categoria_id` FOREIGN KEY (`categoria_id`) REFERENCES `dataeasy_categoria` (`id`),
  CONSTRAINT `dataeasy_producto_marca_id_325581b3_fk_dataeasy_marca_id` FOREIGN KEY (`marca_id`) REFERENCES `dataeasy_marca` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataeasy_producto`
--

LOCK TABLES `dataeasy_producto` WRITE;
/*!40000 ALTER TABLE `dataeasy_producto` DISABLE KEYS */;
INSERT INTO `dataeasy_producto` VALUES (1,'Tornillo Phillips','Cabeza Phillips, acero inox.',150,50,'2025-11-16 03:35:08.006325',1,1),(2,'Martillo Carp.','Mango de madera, cabeza acero',25,10,'2025-11-16 03:35:08.037545',2,2),(3,'WD-40 200ml','Aerosol multiusos',75,20,'2025-11-16 03:35:08.068709',3,3),(4,'Cinta Aislante','Negra, 19mm x 10m',150,30,'2025-11-16 03:35:08.106168',4,4),(5,'Guantes Trabajo','Cuero reforzado, talla L',60,15,'2025-11-16 03:35:08.137242',5,1),(6,'Destornillador P','Punta Phillips PH2',40,10,'2025-11-16 03:35:08.152688',2,5),(7,'Sierra Caladora','Modelo GST 650',15,5,'2025-11-16 03:35:08.179092',2,6),(8,'Ampolleta LED','9W, Luz cálida, E27',120,25,'2025-11-16 03:35:08.210044',6,7),(9,'Taladro Percutor','HP1630, 710W',8,3,'2025-11-16 03:35:08.225434',2,8),(10,'Lija Agua Grano','Grano 220',500,100,'2025-11-16 03:35:08.252182',7,1);
/*!40000 ALTER TABLE `dataeasy_producto` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-16  1:12:48
