from __future__ import annotations

import random
from dataclasses import dataclass


class FountainError(ValueError):
    """Raised when fountain coding encounters invalid data."""


@dataclass(frozen=True)
class GenerationInfo:
    """Metadata required to decode a fountain generation."""

    generation_id: int
    source_block_count: int
    block_size: int

    def __post_init__(self) -> None:
        if not 0 <= self.generation_id <= 0xFFFFFFFF:
            raise FountainError(
                "generation_id must fit in 32 bits"
            )

        if self.source_block_count <= 0:
            raise FountainError(
                "source_block_count must be greater than zero"
            )

        if self.block_size <= 0:
            raise FountainError(
                "block_size must be greater than zero"
            )


@dataclass(frozen=True)
class Droplet:
    """One fountain-coded transmission unit."""

    generation_id: int
    droplet_id: int
    seed: int
    indices: tuple[int, ...]
    payload: bytes


def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two equal-length byte strings."""

    if len(a) != len(b):
        raise FountainError(
            "XOR operands must have equal length"
        )

    return bytes(
        x ^ y
        for x, y in zip(a, b)
    )


class FountainEncoder:
    """Simple seeded XOR fountain encoder."""

    def __init__(
        self,
        blocks: list[bytes],
        generation_id: int = 0,
        seed: int = 42,
    ) -> None:
        if not blocks:
            raise FountainError(
                "at least one source block is required"
            )

        block_size = len(blocks[0])

        if block_size == 0:
            raise FountainError(
                "source blocks cannot be empty"
            )

        if any(
            len(block) != block_size
            for block in blocks
        ):
            raise FountainError(
                "all source blocks must have equal length"
            )

        self.blocks = list(blocks)
        self.generation_id = generation_id
        self._rng = random.Random(seed)

    def generate(
        self,
        droplet_id: int,
    ) -> Droplet:
        """Generate one deterministic fountain droplet."""

        seed = self._rng.randrange(0, 2**32)

        rng = random.Random(seed)

        degree = self._choose_degree(
            rng,
            len(self.blocks),
        )

        indices = tuple(
            sorted(
                rng.sample(
                    range(len(self.blocks)),
                    degree,
                )
            )
        )

        payload = bytes(
            len(self.blocks[0])
        )

        for index in indices:
            payload = xor_bytes(
                payload,
                self.blocks[index],
            )

        return Droplet(
            generation_id=self.generation_id,
            droplet_id=droplet_id,
            seed=seed,
            indices=indices,
            payload=payload,
        )

    @staticmethod
    def _choose_degree(
        rng: random.Random,
        block_count: int,
    ) -> int:
        """Choose a small degree for a practical educational fountain."""

        if block_count == 1:
            return 1

        roll = rng.random()

        if roll < 0.50:
            return 1

        if roll < 0.80:
            return min(2, block_count)

        if roll < 0.95:
            return min(3, block_count)

        return min(4, block_count)


class FountainDecoder:
    """GF(2) Gaussian-elimination decoder for XOR fountain droplets."""

    def __init__(
        self,
        source_block_count: int,
        block_size: int,
        generation_id: int | None = None,
    ) -> None:
        if source_block_count <= 0:
            raise FountainError(
                "source_block_count must be greater than zero"
            )

        if block_size <= 0:
            raise FountainError(
                "block_size must be greater than zero"
            )

        if generation_id is not None and not (
            0 <= generation_id <= 0xFFFFFFFF
        ):
            raise FountainError(
                "generation_id must fit in 32 bits"
            )

        self.source_block_count = source_block_count
        self.block_size = block_size
        self.generation_id = generation_id

        self._equations: list[
            tuple[int, bytes]
        ] = []

    def receive(
        self,
        droplet: Droplet,
    ) -> None:
        """Accept one fountain droplet."""

        if (
            self.generation_id is not None
            and droplet.generation_id != self.generation_id
         ):
            raise FountainError(
                "droplet belongs to a different generation"
             )

        if len(droplet.payload) != self.block_size:
            raise FountainError(
                "droplet payload has incorrect size"
            )

        if not droplet.indices:
            raise FountainError(
                "droplet must reference at least one source block"
            )

        mask = 0

        for index in droplet.indices:
            if not 0 <= index < self.source_block_count:
                raise FountainError(
                    "droplet references an invalid source block"
                )

            mask ^= 1 << index

        if mask == 0:
            raise FountainError(
                "droplet contains duplicate source indices"
            )

        self._equations.append(
            (mask, droplet.payload)
        ) 

    def _solve(self) -> dict[int, bytes]:
        """Solve the received equations using GF(2) elimination."""

        rows = [
            [mask, bytearray(payload)]
            for mask, payload in self._equations
            if mask != 0
        ]

        pivot_row = 0

        for column in range(
            self.source_block_count - 1,
            -1,
            -1,
        ):
            bit = 1 << column

            candidate = None

            for row in range(
                pivot_row,
                len(rows),
            ):
                if rows[row][0] & bit:
                    candidate = row
                    break

            if candidate is None:
                continue

            rows[pivot_row], rows[candidate] = (
                rows[candidate],
                rows[pivot_row],
            )

            pivot_mask, pivot_payload = (
                rows[pivot_row]
            )

            for row in range(len(rows)):
                if row == pivot_row:
                    continue

                mask, payload = rows[row]

                if mask & bit:
                    rows[row][0] ^= pivot_mask

                    for i in range(self.block_size):
                        payload[i] ^= pivot_payload[i]

            pivot_row += 1

            if pivot_row == len(rows):
                break

        decoded: dict[int, bytes] = {}

        for mask, payload in rows:
            if mask == 0:
                continue

            if mask & (mask - 1):
                continue

            index = mask.bit_length() - 1

            decoded[index] = bytes(payload)

        return decoded

    @property
    def decoded_count(self) -> int:
        """Number of source blocks currently solvable."""

        return len(self._solve())

    @property
    def complete(self) -> bool:
        """Whether all source blocks can be reconstructed."""

        return (
            self.decoded_count
            == self.source_block_count
        )

    def reconstruct(self) -> list[bytes]:
        """Reconstruct all source blocks."""

        decoded = self._solve()

        if len(decoded) != self.source_block_count:
            raise FountainError(
                "not enough information to reconstruct source data"
            )

        return [
            decoded[index]
            for index in range(self.source_block_count)
        ]
