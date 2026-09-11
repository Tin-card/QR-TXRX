import pytest

from qr_txrx.transport.packet import Packet, PacketError


def test_packet_roundtrip():
    packet = Packet(
        session_id=12345,
        sequence=7,
        payload=b"hello QR TXRX",
    )

    encoded = packet.encode()
    decoded = Packet.decode(encoded)

    assert decoded == packet


def test_empty_payload():
    packet = Packet(
        session_id=1,
        sequence=0,
        payload=b"",
    )

    assert Packet.decode(packet.encode()) == packet


def test_corrupted_packet_fails_crc():
    packet = Packet(
        session_id=1,
        sequence=2,
        payload=b"important data",
    )

    encoded = bytearray(packet.encode())

    encoded[-5] ^= 0xFF

    with pytest.raises(PacketError, match="CRC check failed"):
        Packet.decode(bytes(encoded))


def test_invalid_magic():
    packet = Packet(
        session_id=1,
        sequence=2,
        payload=b"test",
    )

    encoded = bytearray(packet.encode())
    encoded[0] = ord("X")

    with pytest.raises(PacketError, match="invalid packet magic"):
        Packet.decode(bytes(encoded))


def test_truncated_packet():
    packet = Packet(
        session_id=1,
        sequence=2,
        payload=b"test",
    )

    encoded = packet.encode()

    with pytest.raises(PacketError):
        Packet.decode(encoded[:-1])
