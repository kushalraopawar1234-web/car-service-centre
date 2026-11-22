"""WSGI entry point used by Gunicorn / Render / Railway / any PaaS."""

from app import app

# Gunicorn looks for a module-level callable named "app".
application = app

if __name__ == "__main__":
    app.run()
