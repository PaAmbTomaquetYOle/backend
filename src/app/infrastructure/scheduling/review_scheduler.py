"""APScheduler-backed trigger for the periodic review sweep (BE-24).

## Approach decision

Two options were on the table: an in-process scheduler (APScheduler/Celery
Beat) started alongside the FastAPI app, or an HTTP endpoint triggered by an
external CronJob (e.g. Kubernetes CronJob hitting the deployed service).

**Chosen: in-process APScheduler, started/stopped in the FastAPI lifespan.**
Rationale:
- No new infrastructure to provision or operate — this project already
  deploys a single FastAPI process (see docker-compose.yml); an external
  CronJob would need its own scheduled resource plus a way to reach the
  service, which doesn't exist for this MVP-stage deployment.
- An HTTP-triggered endpoint would need its own authentication (it can't be
  public — anyone could spam-create review processes) for a caller with no
  other requirement to authenticate against this API, adding an auth
  mechanism whose only purpose is talking to itself.
- The app already starts/stops the Kafka producer/consumer and the Neo4j
  driver from the exact same lifespan hook (see ``main.py``) — an in-process
  scheduler follows the same, already-established pattern instead of
  introducing a new one.
- Trade-off accepted: if the process restarts near the scheduled hour, that
  day's sweep may be skipped. Given the sweep re-evaluates every employee's
  elapsed-since-last-review on each run (see ``ReviewSchedulingPolicy``), a
  skipped day self-heals on the next run — nothing is lost, just delayed.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.dossier_generator import IDossierGenerator
from app.application.ports.event_publisher import IEventPublisher
from app.infrastructure.composition import build_review_scheduling_service
from app.infrastructure.persistence.database import get_engine

logger = logging.getLogger(__name__)


class ReviewScheduler:
    """Runs the periodic review sweep once a day via an in-process APScheduler job."""

    def __init__(
        self,
        hour_utc: int,
        event_publisher: IEventPublisher | None = None,
        dossier_generator: IDossierGenerator | None = None,
    ) -> None:
        """Configure the scheduler.

        Args:
            hour_utc: UTC hour (0-23) at which the daily sweep runs.
            event_publisher: Optional event publisher, forwarded to the
                ReviewSchedulingService's facades so a scheduled review
                publishes the same events a manual trigger would (BE-23).
            dossier_generator: Optional generator, forwarded the same way for
                consistency with the other facades (unused by scheduling
                itself, which only creates/starts processes).
        """
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._hour_utc = hour_utc
        self._event_publisher = event_publisher
        self._dossier_generator = dossier_generator

    def start(self) -> None:
        """Register the daily sweep job and start the scheduler."""
        self._scheduler.add_job(
            self._run_sweep,
            trigger=CronTrigger(hour=self._hour_utc, minute=0),
            id="review_scheduling_sweep",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Review scheduler started (daily sweep at %02d:00 UTC)", self._hour_utc)

    def stop(self) -> None:
        """Stop the scheduler, if running."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Review scheduler stopped")

    async def _run_sweep(self) -> None:
        """Run one scheduling sweep in its own session, logging the outcome.

        Never lets an exception escape — a failed sweep should not crash the
        scheduler; it will simply retry on the next scheduled run.
        """
        try:
            async with AsyncSession(get_engine()) as session:
                service = build_review_scheduling_service(
                    session, self._event_publisher, self._dossier_generator
                )
                result = await service.run_due_reviews()
                logger.info(
                    "Review scheduling sweep complete: %d monthly, %d annual review(s) started",
                    len(result.monthly_started),
                    len(result.annual_started),
                )
        except Exception:
            logger.warning("Review scheduling sweep failed", exc_info=True)
