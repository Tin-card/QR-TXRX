from qr_txrx.application.file_transfer import (
    packetize,
    reassemble,
)
from qr_txrx.codecs.qr.codec import QRCodec
from qr_txrx.transport.packet import Packet
from qr_txrx.transport.sequential import (
    SequentialReceiver,
    SequentialSender,
)
from qr_txrx.utils.integrity import sha256


def test_qr_sequential_file_transfer():
    original_data = (
        b"QR TXRX optical communication test data. "
        * 100
    )

    packets = packetize(
        original_data,
        session_id=42,
        block_size=128,
    )

    original_hash = sha256(original_data)

    sender = SequentialSender(packets)
    receiver = SequentialReceiver()
    codec = QRCodec()

    for packet in sender.frames():
        image = codec.encode(packet.encode())

        received_bytes = codec.decode(image)
        received_packet = Packet.decode(received_bytes)

        receiver.receive(received_packet)

    reconstructed = reassemble(receiver.packets())

    assert reconstructed == original_data
    assert sha256(reconstructed) == original_hash
