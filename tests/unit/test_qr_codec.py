from qr_txrx.codecs.qr.codec import QRCodec
from qr_txrx.transport.packet import Packet


def test_qr_roundtrip():
    codec = QRCodec()

    payload = b"Hello from QR TXRX"

    image = codec.encode(payload)
    decoded = codec.decode(image)

    assert decoded == payload


def test_qr_binary_roundtrip():
    codec = QRCodec()

    payload = bytes(range(256))

    image = codec.encode(payload)
    decoded = codec.decode(image)

    assert decoded == payload


def test_packet_qr_packet_roundtrip():
    packet = Packet(
        session_id=123,
        sequence=17,
        payload=bytes(range(256)),
    )

    codec = QRCodec()

    image = codec.encode(packet.encode())
    decoded = Packet.decode(codec.decode(image))

    assert decoded == packet


def test_qr_many_sequential_frames():
    codec = QRCodec()

    for sequence in range(100):
        packet = Packet(
            session_id=42,
            sequence=sequence,
            payload=(
                b"QR TXRX optical communication test data. "
                * 3
            )[:128],
        )

        image = codec.encode(packet.encode())

        decoded_packet = Packet.decode(
            codec.decode(image)
        )

        assert decoded_packet == packet
