import pytest

from qr_txrx.fec.fountain import (
    Droplet,
    FountainDecoder,
    FountainEncoder,
    FountainError,
    GenerationInfo,
    xor_bytes,
)


def test_xor_bytes() -> None:
    assert xor_bytes(
        b"\x01\x02",
        b"\x03\x04",
    ) == b"\x02\x06"


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


def test_xor_requires_equal_lengths() -> None:
    with pytest.raises(
        FountainError,
        match="equal length",
    ):
        xor_bytes(
            b"abc",
            b"ab",
        )


def test_fountain_droplet_is_deterministic() -> None:
    blocks = [
        b"AAAA",
        b"BBBB",
        b"CCCC",
    ]

    encoder_a = FountainEncoder(
        blocks,
        generation_id=7,
        seed=1234,
    )

    encoder_b = FountainEncoder(
        blocks,
        generation_id=7,
        seed=1234,
    )

    droplets_a = [
        encoder_a.generate(i)
        for i in range(5)
    ]

    droplets_b = [
        encoder_b.generate(i)
        for i in range(5)
    ]

    assert droplets_a == droplets_b


def test_degree_one_droplet_can_be_decoded() -> None:
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
        seed=1,
        indices=(0,),
        payload=blocks[0],
    )

    decoder.receive(droplet)

    assert decoder.decoded_count == 1
    assert not decoder.complete


def test_fountain_reconstructs_source_blocks() -> None:
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
            payload=xor_bytes(
                blocks[0],
                blocks[1],
            ),
        ),
        Droplet(
            generation_id=1,
            droplet_id=2,
            seed=2,
            indices=(1, 2),
            payload=xor_bytes(
                blocks[1],
                blocks[2],
            ),
        ),
    ]

    for droplet in droplets:
        decoder.receive(droplet)

    assert decoder.complete
    assert decoder.reconstruct() == blocks


def test_incomplete_fountain_cannot_reconstruct() -> None:
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

    with pytest.raises(
        FountainError,
        match="not enough information",
    ):
        decoder.reconstruct()


def test_generation_info_accepts_valid_metadata() -> None:
    info = GenerationInfo(
        generation_id=1,
        source_block_count=10,
        block_size=64,
    )

    assert info.generation_id == 1
    assert info.source_block_count == 10
    assert info.block_size == 64


def test_generation_info_rejects_invalid_metadata() -> None:
    with pytest.raises(FountainError):
        GenerationInfo(
            generation_id=1,
            source_block_count=0,
            block_size=64,
        )

    with pytest.raises(FountainError):
        GenerationInfo(
            generation_id=1,
            source_block_count=10,
            block_size=0,
        )


def test_decoder_rejects_different_generation() -> None:
    decoder = FountainDecoder(
        source_block_count=3,
        block_size=4,
        generation_id=42,
    )

    droplet = Droplet(
        generation_id=43,
        droplet_id=1,
        seed=1,
        indices=(0,),
        payload=b"test",
    )

    with pytest.raises(
        FountainError,
        match="different generation",
    ):
        decoder.receive(droplet)


