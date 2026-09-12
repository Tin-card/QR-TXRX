import pytest

from qr_txrx.fec.droplet import (
    decode_droplet,
    encode_droplet,
)
from qr_txrx.fec.fountain import (
    Droplet,
    FountainError,
)


def test_droplet_roundtrip():
    droplet = Droplet(
        generation_id=42,
        droplet_id=17,
        seed=123456,
        indices=(0, 2, 5),
        payload=b"ABCDEFGH",
    )

    encoded = encode_droplet(droplet)
    decoded = decode_droplet(
        encoded,
        block_size=8,
    )

    assert decoded == droplet

def test_decode_rejects_zero_degree() -> None:
    data = (
        b"\x00\x00\x00\x00"  # generation_id
        + b"\x00\x00\x00\x00"  # droplet_id
        + b"\x00\x00\x00\x00"  # seed
        + b"\x00"              # degree = 0
        + b"\x00" * 4          # payload
    )

    with pytest.raises(FountainError, match="degree"):
        decode_droplet(data, block_size=4)


def test_decode_rejects_duplicate_indices() -> None:
    droplet = Droplet(
        generation_id=1,
        droplet_id=2,
        seed=3,
        indices=(0, 0),
        payload=b"test",
    )

    data = encode_droplet(droplet)

    with pytest.raises(
        FountainError,
        match="duplicate source indices",
    ):
        decode_droplet(data, block_size=4)

def test_droplet_roundtrip_single_index():
    droplet = Droplet(
        generation_id=1,
        droplet_id=0,
        seed=99,
        indices=(3,),
        payload=b"1234",
    )

    encoded = encode_droplet(droplet)
    decoded = decode_droplet(
        encoded,
        block_size=4,
    )

    assert decoded == droplet


def test_droplet_roundtrip_multiple_indices():
    droplet = Droplet(
        generation_id=10,
        droplet_id=20,
        seed=30,
        indices=(0, 1, 2, 7),
        payload=b"0123456789",
    )

    encoded = encode_droplet(droplet)
    decoded = decode_droplet(
        encoded,
        block_size=10,
    )

    assert decoded == droplet


def test_droplet_decode_rejects_truncated_data():
    with pytest.raises(FountainError):
        decode_droplet(
            b"\x00" * 12,
            block_size=4,
        )


def test_droplet_decode_rejects_wrong_payload_size():
    droplet = Droplet(
        generation_id=1,
        droplet_id=2,
        seed=3,
        indices=(0,),
        payload=b"ABCDEFGH",
    )

    encoded = encode_droplet(droplet)

    with pytest.raises(FountainError):
        decode_droplet(
            encoded,
            block_size=4,
        )
