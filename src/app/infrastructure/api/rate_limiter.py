"""Shared slowapi ``Limiter`` instance.

Kept in its own module (rather than ``main.py``) so routers can import and
apply it via the ``@limiter.limit(...)`` decorator without a circular import
between ``main.py`` and the routers it registers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
