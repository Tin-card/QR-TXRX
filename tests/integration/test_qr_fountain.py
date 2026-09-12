from qr_txrx.fec.droplet import (
    decode_droplet,
    encode_droplet,
)
from qr_txrx.channel.model import ErasureChannel
from qr_txrx.codecs.qr.codec import QRCodec
from qr_txrx.fec.fountain import (
    Droplet,
    FountainDecoder,
    FountainEncoder,
)
from qr_txrx.utils.integrity import sha256


def split_into_blocks(
    data: bytes,
    block_size: int,
) -> tuple[list[bytes], int]:
    """Split data into fixed-size blocks and pad the final block."""

    if block_size <= 0:
        raise ValueError("block_size must be greater than zero")

    original_size = len(data)

    blocks = [
        data[offset : offset + block_size]
        for offset in range(0, len(data), block_size)
    ]

    if not blocks:
        blocks = [bytes(block_size)]

    if len(blocks[-1]) < block_size:
        blocks[-1] = blocks[-1].ljust(
            block_size,
            b"\x00",
        )

    return blocks, original_size


def test_qr_fountain_transfer_with_frame_loss():
    original_data = (
        b"QR TXRX fountain-coded optical communication "
        b"test data. "
        * 100
    )

    block_size = 64

    source_blocks, original_size = split_into_blocks(
        original_data,
        block_size,
    )

    encoder = FountainEncoder(
        source_blocks,
        generation_id=42,
        seed=1234,
    )

    codec = QRCodec()

    droplets = [
        encoder.generate(droplet_id)
        for droplet_id in range(
            len(source_blocks) + 20
        )
    ]

    channel = ErasureChannel(
        loss_rate=0.20,
        seed=42,
    )

    decoder = FountainDecoder(
        source_block_count=len(source_blocks),
        block_size=block_size,
    )

    transmitted = 0
    received = 0

    max_droplets = len(source_blocks) * 3

    while (
        not decoder.complete
        and transmitted < max_droplets
    ):
        droplet = encoder.generate(transmitted)

        image = codec.encode(
            encode_droplet(droplet)
        )

        transmitted += 1

        received_images = channel.transmit([image])

        for received_image in received_images:
            received += 1

            payload = codec.decode(received_image)
            received_droplet = decode_droplet(
                payload,
                block_size=block_size,
             )
            decoder.receive(received_droplet)

    assert decoder.complete, (
        f"Fountain decoding failed: "
        f"source_blocks={len(source_blocks)}, "
        f"transmitted={transmitted}, "
        f"received={received}, "
        f"decoded={decoder.decoded_count}"
    )

    reconstructed = b"".join(
        decoder.reconstruct()
    )[:original_size]

    assert reconstructed == original_data
    assert sha256(reconstructed) == sha256(original_data)

    assert received < transmitted


