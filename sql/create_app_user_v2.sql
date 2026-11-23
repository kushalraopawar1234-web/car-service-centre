-- =====================================================================
-- Create the app login with a password that satisfies any MySQL
-- validate_password policy (upper + lower + digit + special, 15 chars).
--
-- Run as root, press ⚡ once. If anything turns red, send me the
-- "Error Code: xxxx" line.
-- =====================================================================

USE car_service;

-- 1. Login first, so a later problem cannot block it
DROP USER IF EXISTS 'car_app'@'localhost';
DROP USER IF EXISTS 'car_app'@'127.0.0.1';

CREATE USER 'car_app'@'localhost' IDENTIFIED BY 'CarApp#2026!Reva';
CREATE USER 'car_app'@'127.0.0.1' IDENTIFIED BY 'CarApp#2026!Reva';

GRANT SELECT, INSERT, UPDATE, DELETE ON car_service.* TO 'car_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON car_service.* TO 'car_app'@'127.0.0.1';
FLUSH PRIVILEGES;

-- 2. Rebuild the view the app expects (safe to repeat)
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

-- 3. Verify
SELECT user, host, plugin FROM mysql.user WHERE user = 'car_app';

SELECT COUNT(*) AS bills FROM job_bill;

SELECT job_id, reg_no, customer, total
FROM job_bill
ORDER BY job_id
LIMIT 5;

SELECT 'car_service is ready for the app' AS `status`;
