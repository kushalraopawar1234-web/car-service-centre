-- =====================================================================
-- Connect the Flask app to the existing `car_service` schema.
-- Run this in the connected tab (new connection / root), then press ⚡.
-- =====================================================================

-- 1. Verify the data is all there (expect 10 12 5 6 10 12 16 12)
SELECT
  (SELECT COUNT(*) FROM car_service.customer)     AS customers,
  (SELECT COUNT(*) FROM car_service.vehicle)      AS vehicles,
  (SELECT COUNT(*) FROM car_service.mechanic)     AS mechanics,
  (SELECT COUNT(*) FROM car_service.service_type) AS services,
  (SELECT COUNT(*) FROM car_service.spare_part)   AS parts,
  (SELECT COUNT(*) FROM car_service.job_card)     AS jobs,
  (SELECT COUNT(*) FROM car_service.job_part)     AS job_parts,
  (SELECT COUNT(*) FROM car_service.job_bill)     AS bill_rows;

-- 2. Confirm the view works
SELECT job_id, reg_no, customer, service_charge, parts_cost, total
FROM car_service.job_bill
ORDER BY job_id;

-- 3. Create the app login (safe to run repeatedly)
DROP USER IF EXISTS 'car_app'@'localhost';
DROP USER IF EXISTS 'car_app'@'127.0.0.1';

CREATE USER 'car_app'@'localhost' IDENTIFIED BY 'CarApp2026reva';
CREATE USER 'car_app'@'127.0.0.1' IDENTIFIED BY 'CarApp2026reva';

GRANT SELECT, INSERT, UPDATE, DELETE ON car_service.* TO 'car_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON car_service.* TO 'car_app'@'127.0.0.1';
FLUSH PRIVILEGES;

-- 4. Confirm
SELECT user, host, plugin FROM mysql.user WHERE user = 'car_app';

SELECT 'car_service is ready for the app' AS `status`;
