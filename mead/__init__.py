"""Mead CMF — application package.

Entry point: delegates to the core factory with plugin auto-discovery.
``flask run`` / ``gunicorn mead:app`` work out of the box.
"""
from mead.core.app import create_app

app = create_app()
