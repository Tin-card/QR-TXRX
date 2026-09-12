import pytest

from qr_txrx.fec.fountain import (
    Droplet,
    FountainDecoder,
    FountainEncoder,
    FountainError,
    xor_bytes,
)


def test_xor_bytes():
    a = bytes([0xAA, 0x55, 0xFF])
    b = bytes([0xFF, 0x55, 0xAA])

    assert xor_bytes(a, b) == bytes([0x55, 0x00, 0x55])


def test_decoder_rejects_invalid_source_index() -> None:
    decoder = FountainDecoder(
        source_block_count=3,
        block_size=4,
    )

    droplet = Droplet(
        generation_id=1,
        droplet_id=1,
        seed=1,
        indices=(0, 3),
        payload=b"test",
    )

    with pytest.raises(
        FountainError,
        match="invalid source block",
    ):
        decoder.receive(droplet)

def test_xor_requires_equal_lengths():
    with pytest.raises(FountainError):
        xor_bytes(b"abc", b"ab")


def test_fountain_droplet_is_deterministic():
    blocks = [
        b"AAAA",
        b"BBBB",
        b"CCCC",
        b"DDDD",
    ]

    encoder_a = FountainEncoder(
        blocks,
        generation_id=1,
        seed=42,
    )

    encoder_b = FountainEncoder(
        blocks,
        generation_id=1,
        seed=42,
    )

    droplets_a = [
        encoder_a.generate(i)
        for i in range(20)
    ]

    droplets_b = [
        encoder_b.generate(i)
        for i in range(20)
    ]

    assert droplets_a == droplets_b


def test_degree_one_droplet_can_be_decoded():
    blocks = [
        b"AAAA",
        b"BBBB",
        b"CCCC",
    ]

    decoder = FountainDecoder(
        source_block_count=3,
        block_size=4,
    )

    droplet = Droplet(
        generation_id=1,
        droplet_id=0,
        seed=0,
        indices=(1,),
        payload=b"BBBB",
    )

    decoder.receive(droplet)

    assert decoder.decoded_count == 1
    assert not decoder.complete


def test_fountain_reconstructs_source_blocks():
    blocks = [
        b"AAAA",
        b"BBBB",
        b"CCCC",
    ]

    decoder = FountainDecoder(
        source_block_count=3,
        block_size=4,
    )

    droplets = [
        Droplet(
            generation_id=1,
            droplet_id=0,
            seed=0,
            indices=(0,),
            payload=b"AAAA",
        ),
        Droplet(
            generation_id=1,
            droplet_id=1,
            seed=1,
            indices=(0, 1),
            payload=xor_bytes(b"AAAA", b"BBBB"),
        ),
        Droplet(
            generation_id=1,
            droplet_id=2,
            seed=2,
            indices=(1, 2),
            payload=xor_bytes(b"BBBB", b"CCCC"),
        ),
    ]

    for droplet in droplets:
        decoder.receive(droplet)

    assert decoder.complete
    assert decoder.reconstruct() == blocks


def test_incomplete_fountain_cannot_reconstruct():
    decoder = FountainDecoder(
        source_block_count=3,
        block_size=4,
    )

    decoder.receive(
        Droplet(
            generation_id=1,
            droplet_id=0,
            seed=0,
            indices=(0,),
            payload=b"AAAA",
        )
    )

    assert not decoder.complete

    with pytest.raises(FountainError):
        decoder.reconstruct()
