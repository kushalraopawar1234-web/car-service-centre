# Car Service Centre Management System

DBMS Mini Project · REVA University

A Flask + MySQL 8 web application for a car service centre. It manages customers,
vehicles, mechanics, services, spare parts and job cards, tracks parts used on each
job, prints bills, and runs 12 SQL reports.

**Team:** Manoj (Flask) · Mithilesh (HTML/CSS/JS) · Manjunath (connector + queries) · Kushal (MySQL)

---

## 1. Requirements

- Python 3.9 or newer
- MySQL **8.0.16 or newer** (CHECK constraints are only enforced from 8.0.16)
- `flask` and `mysql-connector-python` (see `requirements.txt`)

---

## 2. Create and load the database

From the project root (`car_service/`):

**macOS / Linux**

```bash
mysql -u root -p < sql/database.sql
```

**Windows PowerShell**

```powershell
Get-Content -Raw .\sql\database.sql | mysql -u root -p
```

If `mysql` is not on your PATH, use the full path, for example:

```powershell
Get-Content -Raw .\sql\database.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

This drops and recreates `car_service_db`, creates all seven tables, inserts the
sample data, and creates the `job_bill` view. The script ends with a count summary:

```text
customers  vehicles  mechanics  services  parts  jobs  job_parts  bill_rows
       10        12          5         6     10    12         16         12
```

To run only the 12 report queries:

**macOS / Linux**

```bash
mysql -u root -p < sql/queries.sql
```

**Windows PowerShell**

```powershell
Get-Content -Raw .\sql\queries.sql | mysql -u root -p
```

---

## 3. Install and run

### Windows (PowerShell)

```powershell
cd car_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASS = "your_mysql_password"

python app.py
```

Open <http://127.0.0.1:5000>.

If PowerShell blocks the activation script, run this once in the current window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### macOS / Linux

```bash
cd car_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DB_HOST=localhost
export DB_USER=root
export DB_PASS='your_mysql_password'

python app.py
```

Open <http://127.0.0.1:5000>.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_USER` | `root` | MySQL user |
| `DB_PASS` | empty | MySQL password |
| `DB_PORT` | `3306` | Optional MySQL port |
| `DB_NAME` | `car_service_db` | Optional database name |
| `SECRET_KEY` | development key | Optional Flask session key |
| `FLASK_DEBUG` | `0` | Set to `1` for Flask debug mode |

---

## 4. Demo script: the five constraint failures

The forms do not pre-empt these business rules, so the database is the final
authority. Every failure is caught and shown as a red flash message, and the form
keeps the values you typed.

### 4.1 Duplicate registration number (`UNIQUE`)

1. Open **Vehicles → + Add Vehicle**.
2. Enter `KA01AB1234` (already used by Ravi Kumar's Swift), make `Maruti`,
   model `Swift`, year `2019`, owner `Ravi Kumar`.
3. Submit.

Expected flash:

```text
That value is already in use (UNIQUE constraint).
Duplicate entry 'KA01AB1234' for key 'vehicle.reg_no'
```

### 4.2 Negative service charge (`CHECK`)

1. Open **Services → + Add Service**.
2. Enter service name `Test Wash` and charge `-100`.
3. Submit.

Expected flash:

```text
The database rejected this value because it breaks a validation rule (CHECK constraint).
Check constraint 'chk_service_charge' is violated.
```

### 4.3 End date before start date (`CHECK`)

1. Open **Job Cards → + Add Job Card**.
2. Choose any vehicle, mechanic and service.
3. Set start date `2026-11-10`, end date `2026-11-05`, status `Pending`.
4. Submit.

Expected flash:

```text
The database rejected this value because it breaks a validation rule (CHECK constraint).
Check constraint 'chk_job_dates' is violated.
```

### 4.4 Job for a missing vehicle (`FOREIGN KEY`)

The vehicle dropdown only offers real vehicles, so use SQL to show the constraint,
or post a tampered `vehicle_id` to the form.

SQL:

```sql
USE car_service_db;
INSERT INTO job_card (vehicle_id, mechanic_id, service_id, start_date, status)
VALUES (999, 1, 1, '2026-11-10', 'Pending');
```

Expected:

```text
ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails
(`car_service_db`.`job_card`, CONSTRAINT `fk_job_vehicle` FOREIGN KEY (`vehicle_id`)
REFERENCES `vehicle` (`vehicle_id`))
```

The app maps error 1452 to:

```text
The selected record does not exist, so the foreign key was rejected.
```

To see it in the UI, submit a tampered form (the `vehicle_id` option does not exist):

```bash
curl -i -X POST http://127.0.0.1:5000/job_card/add \
  -d "vehicle_id=999" -d "mechanic_id=1" -d "service_id=1" \
  -d "start_date=2026-11-10" -d "status=Pending"
```

The response is HTTP 400 with the flash message on the form.

### 4.5 Part quantity above stock (`CHECK`, transaction rollback)

1. Open **Parts Used → + Add Part Used**.
2. Choose job card `#1`, spare part `Brake Disc` (stock is 4), quantity `999`.
3. Submit.

Expected flash:

```text
The database rejected this value because it breaks a validation rule (CHECK constraint).
Check constraint 'chk_part_stock' is violated.
```

Verify that the transaction rolled back completely:

```sql
USE car_service_db;
SELECT stock_qty FROM spare_part WHERE part_id = 5;              -- still 4
SELECT * FROM job_part WHERE job_id = 1 AND part_id = 5;         -- no row
```

The app inserts the `job_part` row first, then reduces stock. When the stock
`CHECK` fails, the rollback removes the inserted row as well.

### SQL equivalents for all five

```sql
USE car_service_db;

-- 1. duplicate reg_no (UNIQUE)
INSERT INTO vehicle (reg_no, make, model, year, customer_id)
VALUES ('KA01AB1234', 'Maruti', 'Swift', 2019, 1);

-- 2. negative charge (CHECK)
INSERT INTO service_type (service_name, charge) VALUES ('Bad Service', -100);

-- 3. end date before start date (CHECK)
INSERT INTO job_card (vehicle_id, mechanic_id, service_id, start_date, end_date)
VALUES (1, 1, 1, '2026-11-10', '2026-11-05');

-- 4. missing vehicle (FOREIGN KEY)
INSERT INTO job_card (vehicle_id, mechanic_id, service_id, start_date)
VALUES (999, 1, 1, '2026-11-10');

-- 5. quantity above stock (CHECK + rollback)
START TRANSACTION;
INSERT INTO job_part (job_id, part_id, quantity, unit_price)
VALUES (1, 5, 999, 2200.00);
UPDATE spare_part SET stock_qty = stock_qty - 999 WHERE part_id = 5;
ROLLBACK;
```

---

## 5. Project structure

```text
car_service/
├── app.py                  Flask routes, DB helpers, table registry, reports
├── requirements.txt
├── README.md
├── sql/
│   ├── database.sql        Schema, sample data, job_bill view
│   └── queries.sql         The 12 report queries
├── templates/
│   ├── base.html           Navbar, flash messages, footer
│   ├── dashboard.html      KPI cards + open jobs
│   ├── list.html           Searchable list tables
│   ├── form.html           Add/edit forms with FK dropdowns
│   ├── reports.html        12 report tables
│   ├── bill.html           Print-friendly bill
│   └── error.html          Friendly error page
└── static/
    ├── style.css           Responsive UI, badges, print styles
    └── app.js              Nav toggle, delete confirmation, print buttons
```

---

## 6. Design notes

- **Parameterised SQL only.** Values are always passed as `%s` parameters.
- **Table whitelist.** `TABLES` in `app.py` is the only source of table and column
  names. Routes reject anything else with a 404.
- **Connection handling.** One connection per request, stored in `g`, closed in
  `teardown_appcontext`. Every cursor is closed in a `finally` block.
- **Transactions.**
  - Adding a part: `SELECT … FOR UPDATE` the part, insert `job_part` with the
    current `spare_part.price`, then subtract stock. Any failure rolls back both.
  - Removing a part: add the quantity back to stock and delete the `job_part` row
    in the same transaction.
  - Deleting a job card: restore stock for all its parts before deleting the job
    (the `job_part` rows cascade).
- **Escaping.** Jinja autoescaping is on; no template uses `|safe` on user data.
- **Optional fields.** Email, address, mechanic phone, specialization, end date,
  vehicle year, stock quantity and experience years are optional. `customer.phone`
  is `NOT NULL UNIQUE` in the required schema, so the customer form requires it.
- **Errors.** UNIQUE (1062), CHECK (3819), foreign-key (1452/1451), out-of-range
  (1264) and too-long (1406) errors are mapped to readable flash messages.

---

## 7. Verification performed

- `sql/database.sql` and `sql/queries.sql` were executed on **MySQL 8.0.46**.
- All 12 report queries return rows.
- Every list, add, edit, delete, bill and report route was exercised.
- The five constraint demos above were tested, including the stock rollback.
