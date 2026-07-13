"""Shared slowapi ``Limiter`` instance.

Kept in its own module (rather than ``main.py``) so routers can import and
apply it via the ``@limiter.limit(...)`` decorator without a circular import
between ``main.py`` and the routers it registers.

The ``default_limits`` parameter applies a baseline rate limit to every
endpoint automatically; individual endpoints can override this with
``@limiter.limit(...)`` for stricter or more relaxed limits.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.infrastructure.config.settings import get_settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[get_settings().rate_limit_default],
)
