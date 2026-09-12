from qr_txrx.application.file_transfer import split_into_blocks
from qr_txrx.channel.model import ErasureChannel
from qr_txrx.codecs.qr.codec import QRCodec
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
    FountainDecoder,
    FountainEncoder,
    GenerationInfo,
)
from qr_txrx.utils.integrity import sha256


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

    codec = QRCodec()

    generation_info = GenerationInfo(
        generation_id=42,
        source_block_count=len(source_blocks),
        block_size=block_size,
    )

    metadata_frame = encode_frame(
        FountainFrameType.GENERATION_INFO,
        encode_generation_info(generation_info),
    )

    metadata_image = codec.encode(metadata_frame)

    metadata_payload = codec.decode(
        metadata_image,
    )

    metadata_type, metadata_data = decode_frame(
        metadata_payload,
    )

    received_info = decode_generation_info(
        metadata_data,
    )

    assert metadata_type == FountainFrameType.GENERATION_INFO
    assert received_info == generation_info

    encoder = FountainEncoder(
        source_blocks,
        generation_id=42,
        seed=1234,
    )

    channel = ErasureChannel(
        loss_rate=0.20,
        seed=42,
    )

    decoder = FountainDecoder(
        source_block_count=received_info.source_block_count,
        block_size=received_info.block_size,
        generation_id=received_info.generation_id,
    )

    transmitted = 0
    received = 0
    max_droplets = len(source_blocks) * 6

    while (
        not decoder.complete
        and transmitted < max_droplets
    ):
        droplet = encoder.generate(transmitted)

        frame = encode_frame(
            FountainFrameType.DROPLET,
            encode_droplet(droplet),
        )

        image = codec.encode(frame)

        transmitted += 1

        received_images = channel.transmit(
            [image],
        )

        for received_image in received_images:
            received += 1

            payload = codec.decode(
                received_image,
            )

            frame_type, frame_data = decode_frame(
                payload,
            )

            assert frame_type == FountainFrameType.DROPLET

            received_droplet = decode_droplet(
                frame_data,
                block_size=received_info.block_size,
            )

            decoder.receive(
                received_droplet,
            )

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

    assert sha256(reconstructed) == sha256(
        original_data,
    )

    assert received < transmitted
