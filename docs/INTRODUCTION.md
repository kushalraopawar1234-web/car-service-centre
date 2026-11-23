# Car Service Centre Management System

**A DBMS mini project — REVA University**
**Team:** Manoj (Flask) · Mithilesh (HTML/CSS/JS) · Manjunath (connector + queries) · Kushal (MySQL)

**Live application:** https://car-service-centre.onrender.com
**Source code:** https://github.com/kushalraopawar1234-web/car-service-centre

---

## 1. The application

A car service centre runs on paperwork: a customer walks in with a vehicle, a
mechanic is assigned, a service is performed, spare parts are consumed from
stock, and a bill has to be produced that adds the labour charge to the cost of
those parts. Done on paper, three things go wrong — the same customer is entered
twice, parts are billed that were never in stock, and nobody can answer
"how much did we earn last month?" without reading every register.

The Car Service Centre Management System replaces that paperwork with a single
relational database and a web front end. It is built as a classic three-layer
application: a **MySQL 8 database** that stores the data and enforces its own
rules, a **Flask (Python) application** that validates input and issues SQL, and
**server-rendered HTML pages** that any browser on any device can open. There is
no installation for the user and no data stored inside the web application
itself — every record lives in MySQL.

## 2. What it does

The system manages seven related entities: **customers, vehicles, mechanics,
service types, spare parts, job cards, and the parts used on each job**.

- **Full CRUD on all seven entities** — create, read, update and delete, with
  forms that validate before submission.
- **Search** across every list page (name, phone, registration number, status,
  and so on) using parameterised `LIKE` queries.
- **Foreign-key dropdowns** — a job card can only be created for a vehicle,
  mechanic and service that actually exist, because the options are loaded from
  the parent tables.
- **Job cards** that track a service from `Pending` to `In Progress` to
  `Completed`, with start and end dates.
- **Parts-used tracking with automatic stock control** — adding a part to a job
  copies its current price onto the job and reduces stock in the same
  transaction; removing it or deleting the job restores that stock.
- **Printable bills** — a professional invoice per job showing the service
  charge, every part with quantity and unit price, and the grand total.
- **A dashboard** with live counts and total revenue, and **12 SQL reports**
  covering pending work, mechanic workload, repeat customers, most-used parts,
  low stock, above-average services, customers who never booked, revenue per
  mechanic, and more.

## 3. How it is built (technical overview)

**Database.** Seven tables in third normal form, plus one view. The schema is
where the real work is:

- **6 foreign keys** with deliberately different rules — `RESTRICT` where history
  must not be lost (a vehicle with job cards cannot be deleted), `CASCADE` where
  a child row is meaningless alone (a part line disappears with its job card).
- **8 CHECK constraints** enforcing domain rules inside the database itself —
  vehicle year ≥ 1980, service charge > 0, part price > 0, stock never negative,
  end date never before start date, non-negative experience and quantity.
- **`UNIQUE`** on customer phone, registration number, service name and part name,
  so duplicates are rejected by MySQL, not merely discouraged by the form.
- **`DECIMAL(8,2)`** for all money, because binary floating point cannot represent
  currency exactly and errors compound inside `SUM()`.
- **A composite primary key** `(job_id, part_id)` on the parts table, which makes
  it impossible to list the same part twice on one job.
- **A view, `job_bill`**, that hides a four-table join and a `SUM` aggregate
  behind one name. Every bill, dashboard figure and revenue report reads from it,
  so "total" is defined in exactly one place.

**Application.** Flask with `mysql-connector-python`. All access is
**parameterised SQL**, so user input can never alter the query structure; table
and column names are drawn from a whitelist dictionary in code, never from the
URL. One connection is opened per request and closed by a teardown hook, since
MySQL connections are not thread-safe. Multi-step operations use explicit
transactions with `SELECT … FOR UPDATE` row locks, so two simultaneous requests
cannot oversell the same stock, and a `CHECK` failure rolls back the entire
operation rather than leaving a half-written record. MySQL errors are translated
into readable messages (duplicate value, constraint violation, record still in
use) instead of exposing raw error codes.

**Reports.** The twelve queries deliberately cover the syllabus: inner and left
joins, `GROUP BY` with `HAVING`, scalar subqueries, `NOT EXISTS` anti-joins,
aggregate statistics, and view-based reporting.

**Deployment.** The application is live on **Render** (Gunicorn, 2 workers × 4
threads) against a managed **Aiven MySQL 8.4** instance over TLS. All connection
settings come from environment variables, so the same code runs unchanged on a
laptop and in the cloud. A `/healthz` endpoint verifies the database connection
and is used by the platform to confirm each deploy.

## 4. My role and contribution

I was responsible for the **database layer** of this project.

- Designed the seven-table schema, choosing keys, data types and relationships,
  and normalising the design to third normal form.
- Wrote `sql/database.sql` — table definitions, all 8 CHECK constraints, the 6
  foreign keys with their individual delete rules, the sample dataset, and the
  `job_bill` view.
- Wrote the twelve report queries in `sql/queries.sql`, and the versions served
  by the reports page.
- Verified the database independently: executed every table definition and every
  report query on MySQL 8.0.46, and confirmed the view's totals by hand against
  the parts lines.
- Ran the constraint and transaction tests — duplicate registration number,
  negative service charge, end date before start date, a job card for a
  non-existent vehicle, and a part request exceeding available stock — confirming
  that MySQL rejects each one and that the stock rollback leaves no partial row
  behind.
- Reviewed the SQL embedded in the Flask routes written by the team, to confirm
  that every statement was parameterised and that the transaction boundaries were
  correct.
- Handled deployment: created the cloud MySQL instance, loaded the schema with
  `init_db.py`, configured the environment variables, and verified every route
  and report on the public URL.

The Flask routes and the HTML/CSS were written by my teammates; my contribution
is the schema, the constraints, the view, the queries and the verification that
they behave correctly.

## 5. Summary

The project demonstrates that correctness belongs in the database. The forms
validate, but the database is what guarantees that a registration number is
unique, that a charge is positive, that stock never goes negative, that a bill
can never reference a vehicle that does not exist, and that a failed parts
operation leaves nothing behind. The web application is the interface; MySQL is
the authority.
