from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.offboarding import OffboardingProcessId


class OffboardingProcess:
    __id: OffboardingProcessId