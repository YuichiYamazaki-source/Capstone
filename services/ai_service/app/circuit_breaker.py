"""Lightweight circuit breaker for external service calls.

States:
  CLOSED  → Normal operation. Failures increment counter.
  OPEN    → Too many failures. Calls skip immediately to fallback.
  HALF_OPEN → Recovery probe. One call allowed through to test recovery.

Usage:
    breaker = CircuitBreaker("openai-embedding")
    try:
        result = await breaker.call(some_async_func, arg1, arg2)
    except CircuitOpenError:
        # Use fallback path
"""

import asyncio
import logging
import time
from enum import Enum

from app.config import settings

logger = logging.getLogger("ai-service.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when the circuit is open and calls are rejected."""


class CircuitBreaker:
    """Async-safe circuit breaker with configurable thresholds.

    Args:
        name: Identifier for logging.
        failure_threshold: Consecutive failures before opening the circuit.
        recovery_timeout: Seconds to wait before transitioning to half-open.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int | None = None,
        recovery_timeout: float | None = None,
    ):
        self.name = name
        self.failure_threshold = (
            failure_threshold or settings.circuit_breaker_failure_threshold
        )
        self.recovery_timeout = (
            recovery_timeout or settings.circuit_breaker_recovery_timeout
        )
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Return the current circuit state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if the circuit is open (rejecting calls)."""
        return self._state == CircuitState.OPEN

    async def call(self, func, *args, **kwargs):
        """Execute an async function through the circuit breaker.

        Args:
            func: Async callable to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result of func.

        Raises:
            CircuitOpenError: If the circuit is open and recovery timeout
                has not elapsed.
        """
        async with self._lock:
            self._maybe_transition_to_half_open()

            if self._state == CircuitState.OPEN:
                logger.warning(
                    "Circuit open, rejecting call",
                    extra={"circuit": self.name},
                )
                raise CircuitOpenError(f"Circuit '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    def _maybe_transition_to_half_open(self) -> None:
        """Transition from OPEN to HALF_OPEN if recovery timeout has elapsed."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    "Circuit half-open, allowing probe",
                    extra={
                        "circuit": self.name,
                        "elapsed_s": round(elapsed, 1),
                    },
                )

    async def _on_success(self) -> None:
        """Reset the circuit on a successful call."""
        async with self._lock:
            if self._state in (CircuitState.HALF_OPEN, CircuitState.CLOSED):
                self._failure_count = 0
                if self._state == CircuitState.HALF_OPEN:
                    logger.info(
                        "Circuit recovered, closing",
                        extra={"circuit": self.name},
                    )
                self._state = CircuitState.CLOSED

    async def _on_failure(self) -> None:
        """Increment failure count and potentially open the circuit."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Half-open probe failed, reopening circuit",
                    extra={"circuit": self.name},
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit opened after consecutive failures",
                    extra={
                        "circuit": self.name,
                        "failures": self._failure_count,
                        "threshold": self.failure_threshold,
                    },
                )


# Singleton instances for external services
embedding_circuit = CircuitBreaker("openai-embedding")
qdrant_circuit = CircuitBreaker("qdrant")
