-- =====================================================================
-- Fix / verify the car_service_db setup in MySQL 8.0
-- Connect as root, then click the lightning bolt (Execute).
-- =====================================================================

-- 1. Does the database exist?
SELECT
  COUNT(*) AS `car_service_db_exists`
FROM information_schema.schemata
WHERE schema_name = 'car_service_db';

-- 2. What objects are inside it?
SELECT table_name AS `Object`, table_type AS `Type`
FROM information_schema.tables
WHERE table_schema = 'car_service_db'
ORDER BY table_type, table_name;

-- 3. Row counts (expect 10 12 5 6 10 12 16 12)
SELECT
  (SELECT COUNT(*) FROM car_service_db.customer)     AS customers,
  (SELECT COUNT(*) FROM car_service_db.vehicle)      AS vehicles,
  (SELECT COUNT(*) FROM car_service_db.mechanic)     AS mechanics,
  (SELECT COUNT(*) FROM car_service_db.service_type) AS services,
  (SELECT COUNT(*) FROM car_service_db.spare_part)   AS parts,
  (SELECT COUNT(*) FROM car_service_db.job_card)     AS jobs,
  (SELECT COUNT(*) FROM car_service_db.job_part)     AS job_parts,
  (SELECT COUNT(*) FROM car_service_db.job_bill)     AS bill_rows;

-- 4. Create the application user (safe to run more than once).
--    Password: CarApp2026reva   (no special characters on purpose)
DROP USER IF EXISTS 'car_app'@'localhost';
DROP USER IF EXISTS 'car_app'@'127.0.0.1';

CREATE USER 'car_app'@'localhost' IDENTIFIED BY 'CarApp2026reva';
CREATE USER 'car_app'@'127.0.0.1' IDENTIFIED BY 'CarApp2026reva';

GRANT SELECT, INSERT, UPDATE, DELETE ON car_service_db.* TO 'car_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON car_service_db.* TO 'car_app'@'127.0.0.1';
FLUSH PRIVILEGES;

-- 5. Confirm the user exists
SELECT user, host, plugin FROM mysql.user WHERE user = 'car_app';

SELECT 'setup complete' AS `status`;
