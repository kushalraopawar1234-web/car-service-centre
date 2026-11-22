"""
Car Service Centre Management System
DBMS Mini Project - REVA University

Flask + MySQL 8.0.16+
All database access is parameterised. Table names come only from the
TABLES registry below, never from user input.
"""

import os
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from mysql.connector import Error

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "reva-dbms-car-service-dev-key")


# ---------------------------------------------------------------------
# Database helpers (one connection per request, always closed)
# ---------------------------------------------------------------------
def db_config():
    """Connection settings from environment variables.

    Local MySQL works with the defaults. Managed MySQL providers (Aiven,
    TiDB Cloud, PlanetScale-style endpoints, Railway, Clever Cloud) need
    DB_HOST / DB_PORT / DB_USER / DB_PASS and usually TLS, which is why
    DB_SSL exists.
    """
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "database": os.getenv("DB_NAME", "car_service_db"),
        "charset": "utf8mb4",
        "autocommit": False,
        "connection_timeout": int(os.getenv("DB_TIMEOUT", "15")),
    }

    if os.getenv("DB_SSL", "0") == "1":
        config["ssl_disabled"] = False
        config["ssl_verify_cert"] = os.getenv("DB_SSL_VERIFY", "0") == "1"

    return config


def get_db():
    """Return the connection for the current request, creating it once."""
    if "db" not in g:
        g.db = mysql.connector.connect(**db_config())
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        try:
            if db.is_connected():
                db.close()
        except Error:
            pass


def query_all(sql, params=()):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def query_one(sql, params=()):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()


def query_with_columns(sql, params=()):
    """Return (rows, column_names) so empty report tables still have headers."""
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
        return rows, columns
    finally:
        cur.close()


def execute_write(sql, params=()):
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, params)
        con.commit()
        return cur.rowcount
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()


@contextmanager
def transaction():
    """Cursor + commit/rollback for multi-statement operations."""
    con = get_db()
    cur = con.cursor(dictionary=True)
    try:
        yield cur
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()


def friendly_db_error(error):
    """Turn a MySQL error into a message a user can act on."""
    errno = getattr(error, "errno", None)
    msg = (getattr(error, "msg", None) or str(error)).strip()

    if errno == 1062:
        return f"That value is already in use (UNIQUE constraint). {msg}"
    if errno == 3819:
        return f"The database rejected this value because it breaks a validation rule (CHECK constraint). {msg}"
    if errno == 1452:
        return f"The selected record does not exist, so the foreign key was rejected. {msg}"
    if errno == 1451:
        return f"This record is still used by other records, so it cannot be deleted. {msg}"
    if errno == 1264:
        return f"A number is outside the range allowed by the database column. {msg}"
    if errno == 1406:
        return f"One of the values is too long for its database column. {msg}"
    if errno in (1045, 1049, 2003, 2005):
        return "Could not connect to the database. Check that MySQL is running and that DB_HOST, DB_USER and DB_PASS are correct."
    return f"Database error: {msg}"


# ---------------------------------------------------------------------
# Table registry: the only place table and column names are defined
# ---------------------------------------------------------------------
TABLES = {
    "customer": {
        "singular": "Customer",
        "plural": "Customers",
        "pk": "customer_id",
        "order_by": "c.customer_id ASC",
        "search": ["c.name", "c.phone", "c.email", "c.address"],
        "list_sql": """
            SELECT c.customer_id, c.name, c.phone, c.email, c.address,
                   (SELECT COUNT(*) FROM vehicle v WHERE v.customer_id = c.customer_id) AS vehicles
            FROM customer c
        """,
        "columns": [
            {"key": "customer_id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "phone", "label": "Phone"},
            {"key": "email", "label": "Email"},
            {"key": "address", "label": "Address"},
            {"key": "vehicles", "label": "Vehicles", "align": "right"},
        ],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "cast": "str",
             "required": True, "maxlength": 60},
            {"name": "phone", "label": "Phone", "type": "tel", "cast": "str",
             "required": True, "maxlength": 15,
             "help": "Required by the schema and unique across customers."},
            {"name": "email", "label": "Email", "type": "email", "cast": "str",
             "required": False, "maxlength": 80},
            {"name": "address", "label": "Address", "type": "text", "cast": "str",
             "required": False, "maxlength": 120, "full": True},
        ],
    },
    "vehicle": {
        "singular": "Vehicle",
        "plural": "Vehicles",
        "pk": "vehicle_id",
        "order_by": "v.vehicle_id ASC",
        "search": ["v.reg_no", "v.make", "v.model", "c.name"],
        "list_sql": """
            SELECT v.vehicle_id, v.reg_no, v.make, v.model, v.year, c.name AS owner
            FROM vehicle v
            JOIN customer c ON c.customer_id = v.customer_id
        """,
        "columns": [
            {"key": "vehicle_id", "label": "ID"},
            {"key": "reg_no", "label": "Reg. No."},
            {"key": "make", "label": "Make"},
            {"key": "model", "label": "Model"},
            {"key": "year", "label": "Year"},
            {"key": "owner", "label": "Owner"},
        ],
        "fields": [
            {"name": "reg_no", "label": "Registration No.", "type": "text", "cast": "str",
             "required": True, "maxlength": 15, "placeholder": "KA01AB1234"},
            {"name": "make", "label": "Make", "type": "text", "cast": "str",
             "required": True, "maxlength": 30},
            {"name": "model", "label": "Model", "type": "text", "cast": "str",
             "required": True, "maxlength": 30},
            {"name": "year", "label": "Year", "type": "number", "cast": "int",
             "required": False, "help": "Must be 1980 or later (enforced by the database)."},
            {"name": "customer_id", "label": "Owner", "type": "fk", "cast": "int",
             "required": True,
             "fk": {"sql": "SELECT customer_id AS value, name AS label FROM customer ORDER BY name"}},
        ],
    },
    "mechanic": {
        "singular": "Mechanic",
        "plural": "Mechanics",
        "pk": "mechanic_id",
        "order_by": "m.mechanic_id ASC",
        "search": ["m.name", "m.phone", "m.specialization"],
        "list_sql": "SELECT m.mechanic_id, m.name, m.phone, m.specialization, m.experience_years FROM mechanic m",
        "columns": [
            {"key": "mechanic_id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "phone", "label": "Phone"},
            {"key": "specialization", "label": "Specialization"},
            {"key": "experience_years", "label": "Experience (yrs)", "align": "right"},
        ],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "cast": "str",
             "required": True, "maxlength": 60},
            {"name": "phone", "label": "Phone", "type": "tel", "cast": "str",
             "required": False, "maxlength": 15},
            {"name": "specialization", "label": "Specialization", "type": "text", "cast": "str",
             "required": False, "maxlength": 40},
            {"name": "experience_years", "label": "Experience (years)", "type": "number",
             "cast": "int", "required": False, "default": 0,
             "help": "Defaults to 0. Must not be negative (enforced by the database)."},
        ],
    },
    "service_type": {
        "singular": "Service",
        "plural": "Services",
        "pk": "service_id",
        "order_by": "s.service_id ASC",
        "search": ["s.service_name"],
        "list_sql": "SELECT s.service_id, s.service_name, s.charge FROM service_type s",
        "columns": [
            {"key": "service_id", "label": "ID"},
            {"key": "service_name", "label": "Service"},
            {"key": "charge", "label": "Charge", "money": True, "align": "right"},
        ],
        "fields": [
            {"name": "service_name", "label": "Service Name", "type": "text", "cast": "str",
             "required": True, "maxlength": 60},
            {"name": "charge", "label": "Charge (Rs.)", "type": "number", "cast": "decimal",
             "required": True, "step": "0.01",
             "help": "Must be greater than 0 (enforced by the database)."},
        ],
    },
    "spare_part": {
        "singular": "Spare Part",
        "plural": "Spare Parts",
        "pk": "part_id",
        "order_by": "p.part_id ASC",
        "search": ["p.part_name"],
        "list_sql": "SELECT p.part_id, p.part_name, p.price, p.stock_qty FROM spare_part p",
        "columns": [
            {"key": "part_id", "label": "ID"},
            {"key": "part_name", "label": "Part"},
            {"key": "price", "label": "Price", "money": True, "align": "right"},
            {"key": "stock_qty", "label": "Stock", "align": "right"},
        ],
        "fields": [
            {"name": "part_name", "label": "Part Name", "type": "text", "cast": "str",
             "required": True, "maxlength": 60},
            {"name": "price", "label": "Price (Rs.)", "type": "number", "cast": "decimal",
             "required": True, "step": "0.01",
             "help": "Must be greater than 0 (enforced by the database)."},
            {"name": "stock_qty", "label": "Stock Quantity", "type": "number", "cast": "int",
             "required": False, "default": 0,
             "help": "Defaults to 0. Must not be negative (enforced by the database)."},
        ],
    },
    "job_card": {
        "singular": "Job Card",
        "plural": "Job Cards",
        "pk": "job_id",
        "order_by": "j.job_id DESC",
        "search": ["CAST(j.job_id AS CHAR)", "v.reg_no", "c.name", "m.name",
                   "s.service_name", "j.status"],
        "list_sql": """
            SELECT j.job_id, v.reg_no, c.name AS owner, m.name AS mechanic,
                   s.service_name, j.start_date, j.end_date, j.status, b.total
            FROM job_card j
            JOIN vehicle v      ON v.vehicle_id = j.vehicle_id
            JOIN customer c     ON c.customer_id = v.customer_id
            JOIN mechanic m     ON m.mechanic_id = j.mechanic_id
            JOIN service_type s ON s.service_id = j.service_id
            LEFT JOIN job_bill b ON b.job_id = j.job_id
        """,
        "columns": [
            {"key": "job_id", "label": "Job No."},
            {"key": "reg_no", "label": "Vehicle"},
            {"key": "owner", "label": "Owner"},
            {"key": "mechanic", "label": "Mechanic"},
            {"key": "service_name", "label": "Service"},
            {"key": "start_date", "label": "Start", "type": "date"},
            {"key": "end_date", "label": "End", "type": "date"},
            {"key": "status", "label": "Status", "type": "status"},
            {"key": "total", "label": "Total", "money": True, "align": "right"},
        ],
        "fields": [
            {"name": "vehicle_id", "label": "Vehicle", "type": "fk", "cast": "int",
             "required": True,
             "fk": {"sql": """
                 SELECT vehicle_id AS value,
                        CONCAT(reg_no, ' - ', make, ' ', model) AS label
                 FROM vehicle ORDER BY reg_no
             """}},
            {"name": "mechanic_id", "label": "Mechanic", "type": "fk", "cast": "int",
             "required": True,
             "fk": {"sql": "SELECT mechanic_id AS value, name AS label FROM mechanic ORDER BY name"}},
            {"name": "service_id", "label": "Service", "type": "fk", "cast": "int",
             "required": True,
             "fk": {"sql": """
                 SELECT service_id AS value,
                        CONCAT(service_name, ' (Rs. ', FORMAT(charge, 2), ')') AS label
                 FROM service_type ORDER BY service_name
             """}},
            {"name": "start_date", "label": "Start Date", "type": "date", "cast": "date",
             "required": True},
            {"name": "end_date", "label": "End Date", "type": "date", "cast": "date",
             "required": False,
             "help": "Leave blank while the job is open. It cannot be before the start date."},
            {"name": "status", "label": "Status", "type": "select", "cast": "str",
             "required": True, "default": "Pending",
             "options": ["Pending", "In Progress", "Completed"]},
        ],
    },
    "job_part": {
        "singular": "Part Used",
        "plural": "Parts Used",
        "pk": None,
        "order_by": "jp.job_id DESC, p.part_name ASC",
        "search": ["CAST(jp.job_id AS CHAR)", "v.reg_no", "p.part_name"],
        "list_sql": """
            SELECT jp.job_id, v.reg_no, jp.part_id, p.part_name, jp.quantity,
                   jp.unit_price, (jp.quantity * jp.unit_price) AS line_total
            FROM job_part jp
            JOIN job_card j    ON j.job_id = jp.job_id
            JOIN vehicle v     ON v.vehicle_id = j.vehicle_id
            JOIN spare_part p  ON p.part_id = jp.part_id
        """,
        "columns": [
            {"key": "job_id", "label": "Job No."},
            {"key": "reg_no", "label": "Vehicle"},
            {"key": "part_name", "label": "Part"},
            {"key": "quantity", "label": "Qty", "align": "right"},
            {"key": "unit_price", "label": "Unit Price", "money": True, "align": "right"},
            {"key": "line_total", "label": "Line Total", "money": True, "align": "right"},
        ],
        "fields": [
            {"name": "job_id", "label": "Job Card", "type": "fk", "cast": "int",
             "required": True,
             "fk": {"sql": """
                 SELECT j.job_id AS value,
                        CONCAT('#', j.job_id, ' - ', v.reg_no, ' - ', s.service_name) AS label
                 FROM job_card j
                 JOIN vehicle v      ON v.vehicle_id = j.vehicle_id
                 JOIN service_type s ON s.service_id = j.service_id
                 ORDER BY j.job_id DESC
             """}},
            {"name": "part_id", "label": "Spare Part", "type": "fk", "cast": "int",
             "required": True,
             "fk": {"sql": """
                 SELECT part_id AS value,
                        CONCAT(part_name, ' (Rs. ', FORMAT(price, 2), ' / stock ', stock_qty, ')') AS label
                 FROM spare_part ORDER BY part_name
             """}},
            {"name": "quantity", "label": "Quantity", "type": "number", "cast": "int",
             "required": True,
             "help": "Must be greater than 0 and no more than the available stock. "
                     "The price is copied from the spare part automatically."},
        ],
    },
}


# ---------------------------------------------------------------------
# Report definitions (kept in sync with sql/queries.sql)
# ---------------------------------------------------------------------
REPORTS = [
    {
        "id": "q1",
        "title": "Q1 · Pending jobs, oldest first",
        "description": "Jobs still waiting to be started, ordered by start date.",
        "sql": """
            SELECT j.job_id AS `Job No.`, v.reg_no AS `Reg. No.`,
                   c.name AS `Customer`, j.start_date AS `Start Date`
            FROM job_card j
            JOIN vehicle v ON v.vehicle_id = j.vehicle_id
            JOIN customer c ON c.customer_id = v.customer_id
            WHERE j.status = 'Pending'
            ORDER BY j.start_date ASC, j.job_id ASC
        """,
    },
    {
        "id": "q2",
        "title": "Q2 · Vehicles with owner names",
        "description": "Every vehicle joined to its owner.",
        "sql": """
            SELECT v.reg_no AS `Reg. No.`, v.make AS `Make`, v.model AS `Model`,
                   v.year AS `Year`, c.name AS `Owner`, c.phone AS `Phone`
            FROM vehicle v
            JOIN customer c ON c.customer_id = v.customer_id
            ORDER BY c.name ASC, v.reg_no ASC
        """,
    },
    {
        "id": "q3",
        "title": "Q3 · Full job details",
        "description": "Job card joined with vehicle, owner, mechanic and service.",
        "sql": """
            SELECT j.job_id AS `Job No.`, v.reg_no AS `Reg. No.`,
                   c.name AS `Customer`, m.name AS `Mechanic`,
                   s.service_name AS `Service`, j.start_date AS `Start Date`,
                   j.end_date AS `End Date`, j.status AS `Status`
            FROM job_card j
            JOIN vehicle v ON v.vehicle_id = j.vehicle_id
            JOIN customer c ON c.customer_id = v.customer_id
            JOIN mechanic m ON m.mechanic_id = j.mechanic_id
            JOIN service_type s ON s.service_id = j.service_id
            ORDER BY j.job_id ASC
        """,
    },
    {
        "id": "q4",
        "title": "Q4 · Jobs per mechanic",
        "description": "Workload by mechanic; mechanics with no jobs show 0.",
        "sql": """
            SELECT m.mechanic_id AS `Mechanic ID`, m.name AS `Mechanic`,
                   COUNT(j.job_id) AS `Jobs`
            FROM mechanic m
            LEFT JOIN job_card j ON j.mechanic_id = m.mechanic_id
            GROUP BY m.mechanic_id, m.name
            ORDER BY `Jobs` DESC, m.name ASC
        """,
    },
    {
        "id": "q5",
        "title": "Q5 · Vehicles serviced 2 or more times",
        "description": "Repeat customers by vehicle, using GROUP BY and HAVING.",
        "sql": """
            SELECT v.vehicle_id AS `Vehicle ID`, v.reg_no AS `Reg. No.`,
                   v.make AS `Make`, v.model AS `Model`, COUNT(j.job_id) AS `Visits`
            FROM vehicle v
            JOIN job_card j ON j.vehicle_id = v.vehicle_id
            GROUP BY v.vehicle_id, v.reg_no, v.make, v.model
            HAVING COUNT(j.job_id) >= 2
            ORDER BY `Visits` DESC, v.reg_no ASC
        """,
    },
    {
        "id": "q6",
        "title": "Q6 · Most used spare parts",
        "description": "Total quantity consumed, highest first.",
        "sql": """
            SELECT p.part_id AS `Part ID`, p.part_name AS `Part`,
                   SUM(jp.quantity) AS `Units Used`,
                   COUNT(DISTINCT jp.job_id) AS `Jobs`
            FROM spare_part p
            JOIN job_part jp ON jp.part_id = p.part_id
            GROUP BY p.part_id, p.part_name
            ORDER BY `Units Used` DESC, p.part_name ASC
        """,
    },
    {
        "id": "q7",
        "title": "Q7 · Parts with stock below 5",
        "description": "Low-stock parts that need replenishment.",
        "sql": """
            SELECT part_id AS `Part ID`, part_name AS `Part`,
                   stock_qty AS `Stock`, price AS `Price`
            FROM spare_part
            WHERE stock_qty < 5
            ORDER BY stock_qty ASC, part_name ASC
        """,
    },
    {
        "id": "q8",
        "title": "Q8 · Services charging above average",
        "description": "Services whose charge is above the average charge.",
        "sql": """
            SELECT service_id AS `Service ID`, service_name AS `Service`,
                   charge AS `Charge`
            FROM service_type
            WHERE charge > (SELECT AVG(charge) FROM service_type)
            ORDER BY charge DESC, service_name ASC
        """,
    },
    {
        "id": "q9",
        "title": "Q9 · Customers who never booked a job",
        "description": "Customers with no job card against any of their vehicles.",
        "sql": """
            SELECT c.customer_id AS `Customer ID`, c.name AS `Customer`,
                   c.phone AS `Phone`, c.email AS `Email`
            FROM customer c
            WHERE NOT EXISTS (
                SELECT 1
                FROM vehicle v
                JOIN job_card j ON j.vehicle_id = v.vehicle_id
                WHERE v.customer_id = c.customer_id
            )
            ORDER BY c.name ASC
        """,
    },
    {
        "id": "q10",
        "title": "Q10 · Service charge statistics",
        "description": "Minimum, maximum and average service charge.",
        "sql": """
            SELECT MIN(charge) AS `Lowest`, MAX(charge) AS `Highest`,
                   ROUND(AVG(charge), 2) AS `Average`
            FROM service_type
        """,
    },
    {
        "id": "q11",
        "title": "Q11 · Bill for every job",
        "description": "One row per job from the job_bill view.",
        "sql": """
            SELECT job_id AS `Job No.`, reg_no AS `Reg. No.`,
                   customer AS `Customer`, service_name AS `Service`,
                   service_charge AS `Service Charge`, parts_cost AS `Parts Cost`,
                   total AS `Total`
            FROM job_bill
            ORDER BY job_id ASC
        """,
    },
    {
        "id": "q12",
        "title": "Q12 · Revenue per mechanic",
        "description": "Service charge plus parts, grouped by mechanic.",
        "sql": """
            SELECT m.mechanic_id AS `Mechanic ID`, m.name AS `Mechanic`,
                   COUNT(j.job_id) AS `Jobs`,
                   COALESCE(SUM(b.total), 0) AS `Revenue`
            FROM mechanic m
            LEFT JOIN job_card j ON j.mechanic_id = m.mechanic_id
            LEFT JOIN job_bill b ON b.job_id = j.job_id
            GROUP BY m.mechanic_id, m.name
            ORDER BY `Revenue` DESC, m.name ASC
        """,
    },
]


# ---------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------
@app.template_filter("money")
def money_filter(value):
    if value is None:
        return "0.00"
    try:
        return f"{Decimal(value):,.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return value


@app.template_filter("cell")
def cell_filter(value):
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        return f"{value:,.2f}"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y, %H:%M")
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    return value


@app.template_filter("status_class")
def status_class(status):
    return {
        "Pending": "badge-pending",
        "In Progress": "badge-progress",
        "Completed": "badge-completed",
    }.get(status, "badge-neutral")


@app.template_filter("humanize")
def humanize(value):
    return str(value).replace("_", " ").strip().title()


@app.context_processor
def inject_nav():
    return {
        "nav_tables": [(key, meta["plural"]) for key, meta in TABLES.items()],
        "current_year": date.today().year,
    }


# ---------------------------------------------------------------------
# Validation and form helpers
# ---------------------------------------------------------------------
def get_table(table):
    if table not in TABLES:
        abort(404)
    return TABLES[table]


def parse_form(meta):
    """Return (clean data, errors). DB constraints stay the final authority."""
    data, errors = {}, []

    for field in meta["fields"]:
        name = field["name"]
        raw = (request.form.get(name) or "").strip()

        if raw == "":
            if field.get("required"):
                errors.append(f"{field['label']} is required.")
            data[name] = field.get("default")
            continue

        try:
            if field["cast"] == "int":
                data[name] = int(raw)
            elif field["cast"] == "decimal":
                number = Decimal(raw)
                if not number.is_finite():
                    raise InvalidOperation
                data[name] = number
            elif field["cast"] == "date":
                data[name] = date.fromisoformat(raw)
            else:
                data[name] = raw
        except (ValueError, InvalidOperation):
            label = {"int": "whole number", "decimal": "number", "date": "date"}.get(
                field["cast"], "value"
            )
            errors.append(f"{field['label']} must be a valid {label}.")
            data[name] = raw

    return data, errors


def form_values(meta, row=None):
    values = {}
    for field in meta["fields"]:
        name = field["name"]
        if row is not None and name in row:
            value = row[name]
        else:
            value = field.get("default", "")

        if isinstance(value, datetime):
            value = value.date().isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = f"{value:.2f}" if field["cast"] == "decimal" else str(value)
        elif value is None:
            value = ""

        values[name] = value
    return values


def render_form(table, row=None, form_data=None, status=200):
    meta = TABLES[table]
    values = form_data if form_data is not None else form_values(meta, row)
    fk_options = {
        field["name"]: query_all(field["fk"]["sql"])
        for field in meta["fields"]
        if field["type"] == "fk"
    }

    return (
        render_template(
            "form.html",
            table=table,
            meta=meta,
            fields=meta["fields"],
            values=values,
            fk_options=fk_options,
            is_edit=row is not None,
            title=f"{'Edit' if row is not None else 'Add'} {meta['singular']}",
            action=(
                url_for("edit_row", table=table, pk=row[meta["pk"]])
                if row is not None
                else url_for("add_row", table=table)
            ),
            cancel_url=url_for("list_rows", table=table),
            active=table,
        ),
        status,
    )


# ---------------------------------------------------------------------
# Routes: dashboard, reports, bill
# ---------------------------------------------------------------------
@app.route("/")
def dashboard():
    kpi = query_one("""
        SELECT
          (SELECT COUNT(*) FROM customer) AS customers,
          (SELECT COUNT(*) FROM vehicle) AS vehicles,
          (SELECT COUNT(*) FROM job_card WHERE status = 'Pending') AS pending,
          (SELECT COUNT(*) FROM job_card WHERE status = 'In Progress') AS in_progress,
          (SELECT COALESCE(SUM(total), 0) FROM job_bill) AS billed
    """)

    open_jobs = query_all("""
        SELECT b.job_id, b.reg_no, b.customer, b.service_name, b.total,
               j.status, j.start_date
        FROM job_bill b
        JOIN job_card j ON j.job_id = b.job_id
        WHERE j.status <> 'Completed'
        ORDER BY j.start_date ASC, b.job_id ASC
    """)

    return render_template(
        "dashboard.html",
        kpi=kpi,
        open_jobs=open_jobs,
        active="dashboard",
    )


@app.route("/reports")
def reports():
    report_rows = []
    for report in REPORTS:
        rows, columns = query_with_columns(report["sql"])
        report_rows.append({**report, "rows": rows, "columns": columns})

    return render_template("reports.html", reports=report_rows, active="reports")


@app.route("/bill/<int:job_id>")
def bill(job_id):
    bill_row = query_one("SELECT * FROM job_bill WHERE job_id = %s", (job_id,))
    if not bill_row:
        abort(404)

    info = query_one("""
        SELECT j.job_id, j.start_date, j.end_date, j.status,
               v.reg_no, v.make, v.model, v.year,
               c.name AS customer, c.phone, c.email, c.address,
               m.name AS mechanic, s.service_name
        FROM job_card j
        JOIN vehicle v      ON v.vehicle_id = j.vehicle_id
        JOIN customer c     ON c.customer_id = v.customer_id
        JOIN mechanic m     ON m.mechanic_id = j.mechanic_id
        JOIN service_type s ON s.service_id = j.service_id
        WHERE j.job_id = %s
    """, (job_id,))

    parts = query_all("""
        SELECT p.part_name, jp.quantity, jp.unit_price,
               (jp.quantity * jp.unit_price) AS line_total
        FROM job_part jp
        JOIN spare_part p ON p.part_id = jp.part_id
        WHERE jp.job_id = %s
        ORDER BY p.part_name ASC
    """, (job_id,))

    return render_template(
        "bill.html",
        bill=bill_row,
        info=info,
        parts=parts,
        active="job_card",
    )


# ---------------------------------------------------------------------
# Routes: generic list / add / edit / delete
# ---------------------------------------------------------------------
@app.route("/<table>")
def list_rows(table):
    meta = get_table(table)
    search = (request.args.get("q") or "").strip()

    sql = meta["list_sql"]
    params = []
    if search:
        conditions = [f"{column} LIKE %s" for column in meta["search"]]
        sql += " WHERE (" + " OR ".join(conditions) + ")"
        params = [f"%{search}%"] * len(conditions)

    sql += " ORDER BY " + meta["order_by"]
    rows = query_all(sql, tuple(params))

    return render_template(
        "list.html",
        table=table,
        meta=meta,
        rows=rows,
        search=search,
        active=table,
    )


@app.route("/<table>/add", methods=["GET", "POST"])
def add_row(table):
    meta = get_table(table)
    if table == "job_part":
        return redirect(url_for("add_part"))

    if request.method == "GET":
        return render_form(table)

    data, errors = parse_form(meta)
    if errors:
        for message in errors:
            flash(message, "error")
        return render_form(table, form_data=request.form, status=400)

    columns = [field["name"] for field in meta["fields"]]
    placeholders = ", ".join(["%s"] * len(columns))
    sql = (
        f"INSERT INTO `{table}` ({', '.join(f'`{c}`' for c in columns)}) "
        f"VALUES ({placeholders})"
    )

    try:
        execute_write(sql, tuple(data[column] for column in columns))
    except Error as error:
        flash(friendly_db_error(error), "error")
        return render_form(table, form_data=request.form, status=400)

    flash(f"{meta['singular']} added successfully.", "success")
    return redirect(url_for("list_rows", table=table))


@app.route("/<table>/<int:pk>/edit", methods=["GET", "POST"])
def edit_row(table, pk):
    meta = get_table(table)
    if table == "job_part" or meta["pk"] is None:
        abort(404)

    row = query_one(f"SELECT * FROM `{table}` WHERE `{meta['pk']}` = %s", (pk,))
    if not row:
        abort(404)

    if request.method == "GET":
        return render_form(table, row=row)

    data, errors = parse_form(meta)
    if errors:
        for message in errors:
            flash(message, "error")
        return render_form(table, row=row, form_data=request.form, status=400)

    columns = [field["name"] for field in meta["fields"]]
    assignments = ", ".join(f"`{column}` = %s" for column in columns)
    sql = f"UPDATE `{table}` SET {assignments} WHERE `{meta['pk']}` = %s"

    try:
        execute_write(sql, tuple(data[column] for column in columns) + (pk,))
    except Error as error:
        flash(friendly_db_error(error), "error")
        return render_form(table, row=row, form_data=request.form, status=400)

    flash(f"{meta['singular']} updated successfully.", "success")
    return redirect(url_for("list_rows", table=table))


@app.post("/<table>/<int:pk>/delete")
def delete_row(table, pk):
    meta = get_table(table)
    if table == "job_part" or meta["pk"] is None:
        abort(404)
    if table == "job_card":
        return delete_job_card(pk)

    try:
        execute_write(f"DELETE FROM `{table}` WHERE `{meta['pk']}` = %s", (pk,))
    except Error as error:
        flash(friendly_db_error(error), "error")
    else:
        flash(f"{meta['singular']} deleted.", "success")

    return redirect(url_for("list_rows", table=table))


def delete_job_card(job_id):
    """Delete a job and restore stock for every part on it, atomically."""
    try:
        with transaction() as cur:
            cur.execute("SELECT job_id FROM job_card WHERE job_id = %s FOR UPDATE", (job_id,))
            if not cur.fetchone():
                raise ValueError("Job card not found.")

            cur.execute("""
                UPDATE spare_part p
                JOIN job_part jp ON jp.part_id = p.part_id
                SET p.stock_qty = p.stock_qty + jp.quantity
                WHERE jp.job_id = %s
            """, (job_id,))

            cur.execute("DELETE FROM job_card WHERE job_id = %s", (job_id,))
    except ValueError as error:
        flash(str(error), "error")
    except Error as error:
        flash(friendly_db_error(error), "error")
    else:
        flash("Job card deleted and spare-part stock restored.", "success")

    return redirect(url_for("list_rows", table="job_card"))


# ---------------------------------------------------------------------
# Routes: job_part (one transaction per add / remove)
# ---------------------------------------------------------------------
@app.route("/job_part/add", methods=["GET", "POST"])
def add_part():
    if request.method == "GET":
        return render_form("job_part")

    try:
        job_id = int((request.form.get("job_id") or "").strip())
        part_id = int((request.form.get("part_id") or "").strip())
        quantity = int((request.form.get("quantity") or "").strip())
    except ValueError:
        flash("Job card, spare part and quantity are required.", "error")
        return render_form("job_part", form_data=request.form, status=400)

    try:
        with transaction() as cur:
            # Lock the part row so two requests cannot oversell the same stock.
            cur.execute("""
                SELECT price, stock_qty, part_name
                FROM spare_part
                WHERE part_id = %s
                FOR UPDATE
            """, (part_id,))
            part = cur.fetchone()
            if not part:
                raise ValueError("The selected spare part no longer exists.")

            cur.execute("SELECT job_id FROM job_card WHERE job_id = %s", (job_id,))
            if not cur.fetchone():
                raise ValueError("The selected job card no longer exists.")

            cur.execute(
                "SELECT 1 FROM job_part WHERE job_id = %s AND part_id = %s",
                (job_id, part_id),
            )
            if cur.fetchone():
                raise ValueError(
                    "This part is already on the job. Remove it first to change the quantity."
                )

            # unit_price is copied from spare_part.price inside this transaction.
            cur.execute("""
                INSERT INTO job_part (job_id, part_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """, (job_id, part_id, quantity, part["price"]))

            # If quantity is greater than stock, the CHECK fails and the
            # whole transaction (including the INSERT above) is rolled back.
            cur.execute("""
                UPDATE spare_part
                SET stock_qty = stock_qty - %s
                WHERE part_id = %s
            """, (quantity, part_id))
    except ValueError as error:
        flash(str(error), "error")
        return render_form("job_part", form_data=request.form, status=400)
    except Error as error:
        flash(friendly_db_error(error), "error")
        return render_form("job_part", form_data=request.form, status=400)

    flash(f"Part added to job #{job_id} and stock reduced by {quantity}.", "success")
    return redirect(url_for("list_rows", table="job_part"))


@app.post("/job_part/<int:job_id>/<int:part_id>/delete")
def delete_part(job_id, part_id):
    try:
        with transaction() as cur:
            cur.execute("""
                SELECT quantity
                FROM job_part
                WHERE job_id = %s AND part_id = %s
                FOR UPDATE
            """, (job_id, part_id))
            row = cur.fetchone()
            if not row:
                raise ValueError("That part is not on this job.")

            cur.execute("""
                UPDATE spare_part
                SET stock_qty = stock_qty + %s
                WHERE part_id = %s
            """, (row["quantity"], part_id))

            cur.execute(
                "DELETE FROM job_part WHERE job_id = %s AND part_id = %s",
                (job_id, part_id),
            )
    except ValueError as error:
        flash(str(error), "error")
    except Error as error:
        flash(friendly_db_error(error), "error")
    else:
        flash("Part removed and stock restored.", "success")

    return redirect(url_for("list_rows", table="job_part"))


# ---------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_error):
    return (
        render_template(
            "error.html",
            title="Page not found",
            message="The page or record you asked for does not exist.",
        ),
        404,
    )


@app.errorhandler(Error)
def database_error(error):
    app.logger.exception("Database error")
    return (
        render_template(
            "error.html",
            title="Database error",
            message=friendly_db_error(error),
        ),
        500,
    )


# ---------------------------------------------------------------------
# Health check (used by Render / Railway / uptime monitors)
# ---------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    try:
        query_one("SELECT 1 AS ok")
    except Error as error:
        return {"status": "error", "database": friendly_db_error(error)}, 503
    return {"status": "ok", "database": "connected"}


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT") or os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
