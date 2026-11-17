"""The versioned API surface, mounted at ``/api``.

The package name is the URL segment, so modules here hang under ``/api``. The gateway
authenticates every caller before the request reaches the app; each group below declares its own
access rule (``internal`` and ``dashboard`` both declare an anonymous one: ``()``).
"""
