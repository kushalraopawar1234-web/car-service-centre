-- =====================================================================
-- Repair car_service: rebuild the job_bill view + create the app login.
-- Run as root in the connected tab, then press ⚡ once.
-- DDL comes FIRST so nothing can stop it before the user is created.
-- =====================================================================

USE car_service;

-- 1. Rebuild the view with the columns the app expects
DROP VIEW IF EXISTS job_bill;

CREATE VIEW job_bill AS
SELECT
  j.job_id,
  v.reg_no,
  c.name AS customer,
  s.service_name,
  s.charge AS service_charge,
  COALESCE(SUM(jp.quantity * jp.unit_price), 0) AS parts_cost,
  s.charge + COALESCE(SUM(jp.quantity * jp.unit_price), 0) AS total
FROM job_card j
JOIN vehicle v      ON v.vehicle_id = j.vehicle_id
JOIN customer c     ON c.customer_id = v.customer_id
JOIN service_type s ON s.service_id = j.service_id
LEFT JOIN job_part jp ON jp.job_id = j.job_id
GROUP BY j.job_id, v.reg_no, c.name, s.service_name, s.charge;

-- 2. Application login
DROP USER IF EXISTS 'car_app'@'localhost';
DROP USER IF EXISTS 'car_app'@'127.0.0.1';

CREATE USER 'car_app'@'localhost' IDENTIFIED BY 'CarApp2026reva';
CREATE USER 'car_app'@'127.0.0.1' IDENTIFIED BY 'CarApp2026reva';

GRANT SELECT, INSERT, UPDATE, DELETE ON car_service.* TO 'car_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON car_service.* TO 'car_app'@'127.0.0.1';
FLUSH PRIVILEGES;

-- 3. Verify
SELECT user, host, plugin FROM mysql.user WHERE user = 'car_app';

SELECT job_id, reg_no, customer, service_charge, parts_cost, total
FROM job_bill
ORDER BY job_id;

SELECT 'car_service repaired and ready' AS `status`;
