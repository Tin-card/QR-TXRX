from qr_txrx.codecs.qr.codec import QRCodec


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
