from qr_txrx.application.file_transfer import (
    packetize,
    reassemble,
)
from qr_txrx.channel.model import ErasureChannel
from qr_txrx.codecs.qr.codec import QRCodec
from qr_txrx.transport.packet import Packet
from qr_txrx.transport.sequential import (
    SequentialReceiver,
    SequentialSender,
)


def test_qr_sequential_transfer_with_no_loss():
    original_data = (
        b"QR TXRX optical communication test data. "
        * 100
    )

    packets = packetize(
        original_data,
        session_id=42,
        block_size=128,
    )

    sender = SequentialSender(packets)

    channel = ErasureChannel(
        loss_rate=0.0,
        seed=42,
    )

    receiver = SequentialReceiver()
    codec = QRCodec()

    transmitted_frames = (
        codec.encode(packet.encode())
        for packet in sender.frames()
    )

    for image in channel.transmit(transmitted_frames):
        packet_bytes = codec.decode(image)
        packet = Packet.decode(packet_bytes)
        receiver.receive(packet)

    reconstructed = reassemble(receiver.packets())

    assert reconstructed == original_data

def test_qr_sequential_transfer_fails_with_frame_loss():
    original_data = (
        b"QR TXRX optical communication test data. "
        * 100
    )

    packets = packetize(
        original_data,
        session_id=42,
        block_size=128,
    )

    sender = SequentialSender(packets)

    channel = ErasureChannel(
        loss_rate=0.2,
        seed=42,
    )

    receiver = SequentialReceiver()
    codec = QRCodec()

    transmitted_frames = (
        codec.encode(packet.encode())
        for packet in sender.frames()
    )

    for image in channel.transmit(transmitted_frames):
        packet_bytes = codec.decode(image)
        packet = Packet.decode(packet_bytes)
        receiver.receive(packet)

    try:
        reconstructed = reassemble(receiver.packets())
    except ValueError:
        return

    assert reconstructed != original_data
