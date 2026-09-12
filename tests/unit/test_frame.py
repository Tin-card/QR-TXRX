import pytest

from qr_txrx.fec.droplet import (
    decode_droplet,
    decode_generation_info,
    encode_droplet,
    encode_generation_info,
)
from qr_txrx.fec.frame import (
    FountainFrameType,
    decode_frame,
    encode_frame,
)
from qr_txrx.fec.fountain import (
    Droplet,
    FountainError,
    GenerationInfo,
)

def test_fountain_frame_types() -> None:
    assert FountainFrameType.GENERATION_INFO == 1
    assert FountainFrameType.DROPLET == 2


def test_frame_roundtrip() -> None:
    payload = b"test payload"

    encoded = encode_frame(
        FountainFrameType.DROPLET,
        payload,
    )

    frame_type, decoded_payload = decode_frame(encoded)

    assert frame_type == FountainFrameType.DROPLET
    assert decoded_payload == payload


def test_frame_rejects_empty_data() -> None:
    with pytest.raises(
        FountainError,
        match="too short",
    ):
        decode_frame(b"")


def test_frame_rejects_unknown_type() -> None:
    with pytest.raises(
        FountainError,
        match="unknown fountain frame type",
    ):
        decode_frame(b"\xfftest")

def test_droplet_frame_roundtrip() -> None:
    droplet = Droplet(
        generation_id=7,
        droplet_id=12,
        seed=12345,
        indices=(0, 2, 5),
        payload=b"test",
    )

    encoded_droplet = encode_droplet(droplet)

    frame = encode_frame(
        FountainFrameType.DROPLET,
        encoded_droplet,
    )

    frame_type, payload = decode_frame(frame)

    decoded_droplet = decode_droplet(
        payload,
        block_size=4,
    )

    assert frame_type == FountainFrameType.DROPLET
    assert decoded_droplet == droplet

def test_generation_info_frame_roundtrip() -> None:
    info = GenerationInfo(
        generation_id=7,
        source_block_count=88,
        block_size=64,
    )

    encoded_info = encode_generation_info(info)

    frame = encode_frame(
        FountainFrameType.GENERATION_INFO,
        encoded_info,
    )

    frame_type, payload = decode_frame(frame)

    decoded_info = decode_generation_info(payload)

    assert frame_type == FountainFrameType.GENERATION_INFO
    assert decoded_info == info
