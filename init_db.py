"""
Load sql/database.sql into any MySQL server, including managed cloud MySQL
(Aiven, TiDB Cloud, Railway, Clever Cloud, ...) where you only have a
connection string and no `mysql` command-line client.

Usage
-----
    # local MySQL
    set DB_PASS=yourpassword
    python init_db.py

    # managed MySQL (TLS on)
    set DB_HOST=mysql-xxxx.aivencloud.com
    set DB_PORT=12345
    set DB_USER=avnadmin
    set DB_PASS=xxxxxxxx
    set DB_NAME=car_service_db
    set DB_SSL=1
    python init_db.py

Environment variables are the same ones app.py uses. Add --skip-create when
the provider already made the database and your user cannot create one.
"""

import os
import sys

import mysql.connector
from mysql.connector import Error


def split_statements(sql):
    """Split a .sql file on semicolons, respecting quotes and comments."""
    statements, buf = [], []
    i, n = 0, len(sql)
    quote = None

    while i < n:
        ch = sql[i]

        if quote:
            buf.append(ch)
            if ch == "\\" and quote in ("'", '"'):
                if i + 1 < n:
                    buf.append(sql[i + 1])
                    i += 2
                    continue
            elif ch == quote:
                if i + 1 < n and sql[i + 1] == quote:
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
            i += 1
            continue

        if sql.startswith("--", i):
            end = sql.find("\n", i)
            i = n if end == -1 else end
            continue

        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue

        if ch == ";":
            statement = "".join(buf).strip()
            if statement:
                statements.append(statement)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    statement = "".join(buf).strip()
    if statement:
        statements.append(statement)
    return statements


def connect(database=None):
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "charset": "utf8mb4",
        "autocommit": True,
        "connection_timeout": int(os.getenv("DB_TIMEOUT", "30")),
    }
    if database:
        config["database"] = database
    if os.getenv("DB_SSL", "0") == "1":
        config["ssl_disabled"] = False
        config["ssl_verify_cert"] = os.getenv("DB_SSL_VERIFY", "0") == "1"
    return mysql.connector.connect(**config)


def main():
    skip_create = "--skip-create" in sys.argv or os.getenv("SKIP_DB_CREATE", "0") == "1"
    db_name = os.getenv("DB_NAME", "car_service_db")

    here = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(here, "sql", "database.sql")
    with open(sql_path, "r", encoding="utf-8") as handle:
        statements = split_statements(handle.read())

    print(f"Connecting to {os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')} ...")
    connection = connect()
    cursor = connection.cursor()

    ran = skipped = 0
    for statement in statements:
        head = statement.lstrip().upper()

        if skip_create and (head.startswith("DROP DATABASE") or head.startswith("CREATE DATABASE")):
            skipped += 1
            continue

        try:
            cursor.execute(statement)
            while cursor.nextset():
                pass
            ran += 1
        except Error as error:
            if head.startswith(("DROP DATABASE", "CREATE DATABASE")) and error.errno in (1007, 1044, 1045):
                print(f"  skipped (no privilege to create databases): {error.msg}")
                skipped += 1
                continue
            print(f"\nFAILED: {statement[:120]}...\n  {error}")
            cursor.close()
            connection.close()
            sys.exit(1)

    cursor.close()
    connection.close()

    # Verify with a fresh connection to the target database.
    connection = connect(database=db_name)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT (SELECT COUNT(*) FROM customer), (SELECT COUNT(*) FROM vehicle),
               (SELECT COUNT(*) FROM mechanic), (SELECT COUNT(*) FROM service_type),
               (SELECT COUNT(*) FROM spare_part), (SELECT COUNT(*) FROM job_card),
               (SELECT COUNT(*) FROM job_part), (SELECT COUNT(*) FROM job_bill)
    """)
    counts = cursor.fetchone()
    cursor.close()
    connection.close()

    print(f"\nExecuted {ran} statements ({skipped} skipped).")
    print("customers vehicles mechanics services parts jobs job_parts bill_rows")
    print("  ".join(f"{value:>9}" for value in counts))
    print("\nDatabase is ready.")


if __name__ == "__main__":
    main()
