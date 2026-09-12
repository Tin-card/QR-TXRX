from __future__ import annotations

from enum import IntEnum

from qr_txrx.fec.fountain import FountainError


FRAME_HEADER_SIZE = 1


class FountainFrameType(IntEnum):
    """Identify the type of fountain-related frame."""

    GENERATION_INFO = 1
    DROPLET = 2


def encode_frame(
    frame_type: FountainFrameType,
    payload: bytes,
) -> bytes:
    """Wrap a fountain payload with its frame type."""

    if not isinstance(frame_type, FountainFrameType):
        raise FountainError("invalid fountain frame type")

    return bytes([frame_type]) + payload


def decode_frame(
    data: bytes,
) -> tuple[FountainFrameType, bytes]:
    """Separate a fountain frame type from its payload."""

    if len(data) < FRAME_HEADER_SIZE:
        raise FountainError("fountain frame is too short")

    try:
        frame_type = FountainFrameType(data[0])
    except ValueError as exc:
        raise FountainError(
            f"unknown fountain frame type: {data[0]}"
        ) from exc

    return frame_type, data[FRAME_HEADER_SIZE:]
