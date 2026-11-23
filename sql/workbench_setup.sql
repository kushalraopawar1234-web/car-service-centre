-- =====================================================================
-- ONE-CLICK SETUP for MySQL 8.0 Workbench
-- Run this whole file (lightning bolt) while connected as root.
-- It creates car_service_db, all 7 tables, the job_bill view,
-- the sample data, and the car_app user.
-- =====================================================================
-- =====================================================================
-- Car Service Centre Management System
-- DBMS Mini Project - REVA University
--
-- Target: MySQL 8.0.16 or newer (CHECK constraints are enforced from
--         8.0.16 onwards; this script was verified on MySQL 8.0.46).
--
-- Run from the project root:
--   mysql -u root -p < sql/database.sql
-- =====================================================================

DROP DATABASE IF EXISTS car_service_db;
CREATE DATABASE car_service_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE car_service_db;

-- ---------------------------------------------------------------------
-- 1. customer
-- ---------------------------------------------------------------------
CREATE TABLE customer (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(60)  NOT NULL,
  phone       VARCHAR(15)  NOT NULL UNIQUE,
  email       VARCHAR(80),
  address     VARCHAR(120)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 2. vehicle
-- ---------------------------------------------------------------------
CREATE TABLE vehicle (
  vehicle_id  INT AUTO_INCREMENT PRIMARY KEY,
  reg_no      VARCHAR(15) NOT NULL UNIQUE,
  make        VARCHAR(30) NOT NULL,
  model       VARCHAR(30) NOT NULL,
  year        INT,
  customer_id INT         NOT NULL,
  CONSTRAINT chk_vehicle_year CHECK (year >= 1980),
  CONSTRAINT fk_vehicle_customer
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 3. mechanic
-- ---------------------------------------------------------------------
CREATE TABLE mechanic (
  mechanic_id      INT AUTO_INCREMENT PRIMARY KEY,
  name             VARCHAR(60) NOT NULL,
  phone            VARCHAR(15),
  specialization   VARCHAR(40),
  experience_years INT NOT NULL DEFAULT 0,
  CONSTRAINT chk_mechanic_experience CHECK (experience_years >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 4. service_type
-- ---------------------------------------------------------------------
CREATE TABLE service_type (
  service_id   INT AUTO_INCREMENT PRIMARY KEY,
  service_name VARCHAR(60)   NOT NULL UNIQUE,
  charge       DECIMAL(8,2)  NOT NULL,
  CONSTRAINT chk_service_charge CHECK (charge > 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 5. spare_part
-- ---------------------------------------------------------------------
CREATE TABLE spare_part (
  part_id    INT AUTO_INCREMENT PRIMARY KEY,
  part_name  VARCHAR(60)  NOT NULL UNIQUE,
  price      DECIMAL(8,2) NOT NULL,
  stock_qty  INT          NOT NULL DEFAULT 0,
  CONSTRAINT chk_part_price CHECK (price > 0),
  CONSTRAINT chk_part_stock CHECK (stock_qty >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 6. job_card
-- ---------------------------------------------------------------------
CREATE TABLE job_card (
  job_id      INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id  INT  NOT NULL,
  mechanic_id INT  NOT NULL,
  service_id  INT  NOT NULL,
  start_date  DATE NOT NULL,
  end_date    DATE,
  status      ENUM('Pending','In Progress','Completed') NOT NULL DEFAULT 'Pending',
  CONSTRAINT chk_job_dates CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT fk_job_vehicle
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_job_mechanic
    FOREIGN KEY (mechanic_id) REFERENCES mechanic(mechanic_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_job_service
    FOREIGN KEY (service_id) REFERENCES service_type(service_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 7. job_part
-- ---------------------------------------------------------------------
CREATE TABLE job_part (
  job_id     INT           NOT NULL,
  part_id    INT           NOT NULL,
  quantity   INT           NOT NULL,
  unit_price DECIMAL(8,2)  NOT NULL,
  PRIMARY KEY (job_id, part_id),
  CONSTRAINT chk_job_part_qty CHECK (quantity > 0),
  CONSTRAINT chk_job_part_price CHECK (unit_price > 0),
  CONSTRAINT fk_job_part_job
    FOREIGN KEY (job_id) REFERENCES job_card(job_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_job_part_part
    FOREIGN KEY (part_id) REFERENCES spare_part(part_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE = InnoDB;

-- =====================================================================
-- Sample data (Bengaluru)
-- =====================================================================

INSERT INTO customer (name, phone, email, address) VALUES
  ('Ravi Kumar',    '9845012345', 'ravi.kumar@example.com',   'Jayanagar 4th Block, Bengaluru'),
  ('Sneha Reddy',   '9845023456', 'sneha.reddy@example.com',  'Whitefield, Bengaluru'),
  ('Arun Patil',    '9845034567', 'arun.patil@example.com',   'Indiranagar, Bengaluru'),
  ('Meena Iyer',    '9845045678', 'meena.iyer@example.com',   'Koramangala 5th Block, Bengaluru'),
  ('Imran Khan',    '9845056789', 'imran.khan@example.com',   'HSR Layout Sector 2, Bengaluru'),
  ('Divya Nair',    '9845067890', 'divya.nair@example.com',   'Yelahanka New Town, Bengaluru'),
  ('Suresh Gowda',  '9845078901', 'suresh.gowda@example.com', 'Malleshwaram, Bengaluru'),
  ('Pooja Shetty',  '9845089012', 'pooja.shetty@example.com', 'Hebbal, Bengaluru'),
  ('Vikram Rao',    '9845090123', 'vikram.rao@example.com',   'BTM Layout 2nd Stage, Bengaluru'),
  ('Anita Joseph',  '9845001234', 'anita.joseph@example.com', 'Marathahalli, Bengaluru');

INSERT INTO vehicle (reg_no, make, model, year, customer_id) VALUES
  ('KA01AB1234', 'Maruti',  'Swift',  2019, 1),
  ('KA03CD5678', 'Hyundai', 'i20',    2020, 2),
  ('KA05EF9012', 'Honda',   'City',   2018, 3),
  ('KA02GH3456', 'Tata',    'Nexon',  2021, 4),
  ('KA04JK7890', 'Toyota',  'Innova', 2017, 5),
  ('KA51LM1122', 'Maruti',  'Baleno', 2022, 6),
  ('KA53NP3344', 'Kia',     'Seltos', 2021, 7),
  ('KA01QR5566', 'Mahindra','XUV300', 2020, 8),
  ('KA09ST7788', 'Hyundai', 'Creta',  2019, 9),
  ('KA03UV9900', 'Maruti',  'Swift',  2016, 1),
  ('KA05WX2468', 'Honda',   'Amaze',  2020, 2),
  ('KA02YZ1357', 'Renault', 'Kwid',   2018, 10);

INSERT INTO mechanic (name, phone, specialization, experience_years) VALUES
  ('Ramesh',    '9846012345', 'Engine',     12),
  ('Kiran',     '9846023456', 'Electrical',  8),
  ('Lokesh',    '9846034567', 'Brakes',      6),
  ('Nagaraj',   '9846045678', 'AC',         10),
  ('Basavaraj', '9846056789', 'General',     4);

INSERT INTO service_type (service_name, charge) VALUES
  ('General Service',   1800.00),
  ('Oil Change',         900.00),
  ('Brake Repair',      2500.00),
  ('AC Repair',         3200.00),
  ('Wheel Alignment',    700.00),
  ('Engine Diagnosis',  1500.00);

INSERT INTO spare_part (part_name, price, stock_qty) VALUES
  ('Engine Oil 1L',    450.00, 40),
  ('Oil Filter',       250.00, 30),
  ('Air Filter',       300.00, 25),
  ('Brake Pad Set',   1800.00, 12),
  ('Brake Disc',      2200.00,  4),
  ('Spark Plug',       180.00, 50),
  ('Car Battery',     4500.00,  3),
  ('AC Compressor',   8500.00,  2),
  ('Wiper Blade',      220.00, 20),
  ('Coolant 1L',       320.00, 18);

INSERT INTO job_card (vehicle_id, mechanic_id, service_id, start_date, end_date, status) VALUES
  (1, 5, 1, '2026-10-05', '2026-10-06', 'Completed'),
  (2, 1, 2, '2026-10-07', '2026-10-07', 'Completed'),
  (3, 3, 3, '2026-10-10', '2026-10-12', 'Completed'),
  (4, 4, 4, '2026-10-14', '2026-10-16', 'Completed'),
  (5, 1, 6, '2026-10-18', '2026-10-19', 'Completed'),
  (6, 5, 2, '2026-10-20', '2026-10-20', 'Completed'),
  (7, 2, 6, '2026-10-25', NULL,         'In Progress'),
  (8, 3, 3, '2026-10-28', NULL,         'In Progress'),
  (1, 5, 5, '2026-11-02', NULL,         'Pending'),
  (9, 1, 1, '2026-11-03', NULL,         'Pending'),
  (10,5, 2, '2026-11-04', NULL,         'Pending'),
  (3, 3, 3, '2026-11-05', NULL,         'Pending');

INSERT INTO job_part (job_id, part_id, quantity, unit_price) VALUES
  (1,  1, 4,  450.00),
  (1,  2, 1,  250.00),
  (1,  3, 1,  300.00),
  (2,  1, 3,  450.00),
  (2,  2, 1,  250.00),
  (3,  4, 1, 1800.00),
  (3,  5, 2, 2200.00),
  (4,  8, 1, 8500.00),
  (5,  6, 4,  180.00),
  (5,  1, 4,  450.00),
  (6,  1, 3,  450.00),
  (6,  2, 1,  250.00),
  (7,  6, 4,  180.00),
  (8,  4, 1, 1800.00),
  (10, 3, 1,  300.00),
  (10, 1, 4,  450.00);

-- =====================================================================
-- View: one row per job, with service charge + parts cost + total
-- =====================================================================
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

-- ---------------------------------------------------------------------
-- Quick sanity check (optional, prints a small summary)
-- ---------------------------------------------------------------------
SELECT
  (SELECT COUNT(*) FROM customer)  AS customers,
  (SELECT COUNT(*) FROM vehicle)   AS vehicles,
  (SELECT COUNT(*) FROM mechanic)  AS mechanics,
  (SELECT COUNT(*) FROM service_type) AS services,
  (SELECT COUNT(*) FROM spare_part)   AS parts,
  (SELECT COUNT(*) FROM job_card)     AS jobs,
  (SELECT COUNT(*) FROM job_part)     AS job_parts,
  (SELECT COUNT(*) FROM job_bill)     AS bill_rows;

-- =====================================================================
-- PART 2 - Application user (so the Flask app never uses root)
-- =====================================================================
DROP USER IF EXISTS 'car_app'@'localhost';
DROP USER IF EXISTS 'car_app'@'127.0.0.1';

CREATE USER 'car_app'@'localhost' IDENTIFIED BY 'CarApp#2026!reva';
CREATE USER 'car_app'@'127.0.0.1' IDENTIFIED BY 'CarApp#2026!reva';

GRANT SELECT, INSERT, UPDATE, DELETE ON car_service_db.* TO 'car_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON car_service_db.* TO 'car_app'@'127.0.0.1';
FLUSH PRIVILEGES;

-- =====================================================================
-- PART 3 - Verification (you should see these results in Workbench)
-- =====================================================================
SHOW TABLES;

SELECT table_name AS `Object`, table_type AS `Type`
FROM information_schema.tables
WHERE table_schema = 'car_service_db'
ORDER BY table_type, table_name;

SELECT
  (SELECT COUNT(*) FROM customer)     AS customers,
  (SELECT COUNT(*) FROM vehicle)      AS vehicles,
  (SELECT COUNT(*) FROM mechanic)     AS mechanics,
  (SELECT COUNT(*) FROM service_type) AS services,
  (SELECT COUNT(*) FROM spare_part)   AS parts,
  (SELECT COUNT(*) FROM job_card)     AS jobs,
  (SELECT COUNT(*) FROM job_part)     AS job_parts,
  (SELECT COUNT(*) FROM job_bill)     AS bill_rows;

SELECT job_id, reg_no, customer, service_charge, parts_cost, total
FROM job_bill
ORDER BY job_id;
