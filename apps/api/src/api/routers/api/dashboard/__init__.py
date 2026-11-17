"""Dashboard endpoints: monthly KPIs, history, on-the-books future, and a year overview.

The package keeps its name as the URL segment (``route.py`` serves ``/api/dashboard`` and
``/api/dashboard/bootstrap``). The gateway authenticates every caller before the request reaches
the app, so this group declares an anonymous rule: ``()``.
"""

from fastapi import params

dependencies: tuple[params.Depends, ...] = ()
