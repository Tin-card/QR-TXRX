from __future__ import annotations

from qr_txrx.fec.fountain import Droplet, FountainError


HEADER_SIZE = 13


def encode_droplet(droplet: Droplet) -> bytes:
    """Serialize a fountain droplet."""

    result = bytearray()

    result.extend(
        droplet.generation_id.to_bytes(4, "big")
    )

    result.extend(
        droplet.droplet_id.to_bytes(4, "big")
    )

    result.extend(
        droplet.seed.to_bytes(4, "big")
    )

    result.append(len(droplet.indices))

    for index in droplet.indices:
        result.extend(
            index.to_bytes(4, "big")
        )

    result.extend(droplet.payload)

    return bytes(result)


def decode_droplet(
    data: bytes,
    block_size: int,
) -> Droplet:
    """Deserialize a fountain droplet."""

    if len(data) < HEADER_SIZE + block_size:
        raise FountainError(
            "droplet data is too short"
        )

    position = 0

    generation_id = int.from_bytes(
        data[position:position + 4],
        "big",
    )
    position += 4

    droplet_id = int.from_bytes(
        data[position:position + 4],
        "big",
    )
    position += 4

    seed = int.from_bytes(
        data[position:position + 4],
        "big",
    )
    position += 4

    degree = data[position]
    position += 1
    if degree == 0:
     raise FountainError(
         "droplet degree must be greater than zero"
     )

    metadata_size = degree * 4
    payload_start = position + metadata_size

    if len(data) < payload_start + block_size:
        raise FountainError(
            "droplet data is truncated"
        )

    indices = []

    for _ in range(degree):
        index = int.from_bytes(
            data[position:position + 4],
            "big",
        )
        position += 4

        indices.append(index)
    if len(set(indices)) != len(indices):
        raise FountainError(
            "droplet contains duplicate source indices"
        )

    payload = data[position:]

    if len(payload) != block_size:
        raise FountainError(
            "droplet payload has incorrect size"
        )

    return Droplet(
        generation_id=generation_id,
        droplet_id=droplet_id,
        seed=seed,
        indices=tuple(indices),
        payload=payload,
    )
