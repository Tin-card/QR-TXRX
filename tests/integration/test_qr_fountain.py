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

from qr_txrx.application.file_transfer import (
    split_into_blocks,
)



def test_qr_fountain_transfer_with_frame_loss():
    original_data = (
        b"QR TXRX fountain-coded optical communication "
        b"test data. "
        * 100
    )

    block_size = 64


    original_size = len(original_data)

    source_blocks = split_into_blocks(
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


