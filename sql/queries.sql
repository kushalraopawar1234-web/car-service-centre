-- =====================================================================
-- Car Service Centre Management System - Report queries
-- MySQL 8.0.16+ | Database: car_service_db
--
-- Run from the project root:
--   mysql -u root -p < sql/queries.sql
-- =====================================================================

USE car_service_db;

-- ---------------------------------------------------------------------
-- Q1. Pending jobs, oldest first
-- ---------------------------------------------------------------------
SELECT
  j.job_id     AS `Job No.`,
  v.reg_no     AS `Reg. No.`,
  c.name       AS `Customer`,
  j.start_date AS `Start Date`
FROM job_card j
JOIN vehicle v  ON v.vehicle_id = j.vehicle_id
JOIN customer c ON c.customer_id = v.customer_id
WHERE j.status = 'Pending'
ORDER BY j.start_date ASC, j.job_id ASC;

-- ---------------------------------------------------------------------
-- Q2. Vehicles with owner names
-- ---------------------------------------------------------------------
SELECT
  v.reg_no AS `Reg. No.`,
  v.make   AS `Make`,
  v.model  AS `Model`,
  v.year   AS `Year`,
  c.name   AS `Owner`,
  c.phone  AS `Phone`
FROM vehicle v
JOIN customer c ON c.customer_id = v.customer_id
ORDER BY c.name ASC, v.reg_no ASC;

-- ---------------------------------------------------------------------
-- Q3. Full job details
-- ---------------------------------------------------------------------
SELECT
  j.job_id     AS `Job No.`,
  v.reg_no     AS `Reg. No.`,
  c.name       AS `Customer`,
  m.name       AS `Mechanic`,
  s.service_name AS `Service`,
  j.start_date AS `Start Date`,
  j.end_date   AS `End Date`,
  j.status     AS `Status`
FROM job_card j
JOIN vehicle v      ON v.vehicle_id = j.vehicle_id
JOIN customer c     ON c.customer_id = v.customer_id
JOIN mechanic m     ON m.mechanic_id = j.mechanic_id
JOIN service_type s ON s.service_id = j.service_id
ORDER BY j.job_id ASC;

-- ---------------------------------------------------------------------
-- Q4. Jobs per mechanic (includes mechanics with zero jobs)
-- ---------------------------------------------------------------------
SELECT
  m.mechanic_id AS `Mechanic ID`,
  m.name        AS `Mechanic`,
  COUNT(j.job_id) AS `Jobs`
FROM mechanic m
LEFT JOIN job_card j ON j.mechanic_id = m.mechanic_id
GROUP BY m.mechanic_id, m.name
ORDER BY `Jobs` DESC, m.name ASC;

-- ---------------------------------------------------------------------
-- Q5. Vehicles serviced 2 or more times
-- ---------------------------------------------------------------------
SELECT
  v.vehicle_id AS `Vehicle ID`,
  v.reg_no     AS `Reg. No.`,
  v.make       AS `Make`,
  v.model      AS `Model`,
  COUNT(j.job_id) AS `Visits`
FROM vehicle v
JOIN job_card j ON j.vehicle_id = v.vehicle_id
GROUP BY v.vehicle_id, v.reg_no, v.make, v.model
HAVING COUNT(j.job_id) >= 2
ORDER BY `Visits` DESC, v.reg_no ASC;

-- ---------------------------------------------------------------------
-- Q6. Most used spare parts
-- ---------------------------------------------------------------------
SELECT
  p.part_id   AS `Part ID`,
  p.part_name AS `Part`,
  SUM(jp.quantity) AS `Units Used`,
  COUNT(DISTINCT jp.job_id) AS `Jobs`
FROM spare_part p
JOIN job_part jp ON jp.part_id = p.part_id
GROUP BY p.part_id, p.part_name
ORDER BY `Units Used` DESC, p.part_name ASC;

-- ---------------------------------------------------------------------
-- Q7. Parts with stock below 5
-- ---------------------------------------------------------------------
SELECT
  part_id   AS `Part ID`,
  part_name AS `Part`,
  stock_qty AS `Stock`,
  price     AS `Price`
FROM spare_part
WHERE stock_qty < 5
ORDER BY stock_qty ASC, part_name ASC;

-- ---------------------------------------------------------------------
-- Q8. Services charging above the average service charge
-- ---------------------------------------------------------------------
SELECT
  service_id   AS `Service ID`,
  service_name AS `Service`,
  charge       AS `Charge`
FROM service_type
WHERE charge > (SELECT AVG(charge) FROM service_type)
ORDER BY charge DESC, service_name ASC;

-- ---------------------------------------------------------------------
-- Q9. Customers who have never booked a job
-- ---------------------------------------------------------------------
SELECT
  c.customer_id AS `Customer ID`,
  c.name        AS `Customer`,
  c.phone       AS `Phone`,
  c.email       AS `Email`
FROM customer c
WHERE NOT EXISTS (
  SELECT 1
  FROM vehicle v
  JOIN job_card j ON j.vehicle_id = v.vehicle_id
  WHERE v.customer_id = c.customer_id
)
ORDER BY c.name ASC;

-- ---------------------------------------------------------------------
-- Q10. Service charge statistics: minimum, maximum and average
-- ---------------------------------------------------------------------
SELECT
  MIN(charge) AS `Lowest`,
  MAX(charge) AS `Highest`,
  ROUND(AVG(charge), 2) AS `Average`
FROM service_type;

-- ---------------------------------------------------------------------
-- Q11. Bill for every job (uses the job_bill view)
-- ---------------------------------------------------------------------
SELECT
  job_id         AS `Job No.`,
  reg_no         AS `Reg. No.`,
  customer       AS `Customer`,
  service_name   AS `Service`,
  service_charge AS `Service Charge`,
  parts_cost     AS `Parts Cost`,
  total          AS `Total`
FROM job_bill
ORDER BY job_id ASC;

-- ---------------------------------------------------------------------
-- Q12. Revenue per mechanic
-- ---------------------------------------------------------------------
SELECT
  m.mechanic_id AS `Mechanic ID`,
  m.name        AS `Mechanic`,
  COUNT(j.job_id) AS `Jobs`,
  COALESCE(SUM(b.total), 0) AS `Revenue`
FROM mechanic m
LEFT JOIN job_card j ON j.mechanic_id = m.mechanic_id
LEFT JOIN job_bill b ON b.job_id = j.job_id
GROUP BY m.mechanic_id, m.name
ORDER BY `Revenue` DESC, m.name ASC;
