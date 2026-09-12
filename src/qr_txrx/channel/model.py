from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from typing import TypeVar


T = TypeVar("T")


class ErasureChannel:
    """Simulate random frame loss in a communication channel."""

    def __init__(
        self,
        loss_rate: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if not 0.0 <= loss_rate <= 1.0:
            raise ValueError("loss_rate must be between 0 and 1")

        self.loss_rate = loss_rate
        self._rng = random.Random(seed)

    def transmit(self, frames: Iterable[T]) -> Iterator[T]:
        """Yield frames that survive the channel."""

        for frame in frames:
            if self._rng.random() >= self.loss_rate:
                yield frame
