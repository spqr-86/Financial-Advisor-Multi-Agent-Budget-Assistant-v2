"""Graceful shutdown utilities for services."""

import asyncio
import logging
import signal
from typing import Callable

logger = logging.getLogger(__name__)


def setup_shutdown_handlers(shutdown_callback: Callable[[], None]) -> None:
    """
    Set up signal handlers for graceful shutdown.

    Args:
        shutdown_callback: Async function to call on shutdown

    Handles SIGTERM (Cloud Run, Docker) and SIGINT (Ctrl+C).
    """

    def signal_handler(sig: int, frame: any) -> None:
        """Handle shutdown signals."""
        sig_name = signal.Signals(sig).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")

        # Create event loop if needed and run shutdown callback
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(shutdown_callback())
            else:
                loop.run_until_complete(shutdown_callback())
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("Shutdown handlers registered (SIGTERM, SIGINT)")
