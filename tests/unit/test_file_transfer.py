import pytest

from qr_txrx.application.file_transfer import (
    packetize,
    reassemble,
    split_into_blocks,
)


def test_packetize_and_reassemble():
    data = b"Hello QR TXRX!" * 100

    packets = packetize(
        data,
        session_id=123,
        block_size=32,
    )

    assert len(packets) > 1
    assert reassemble(packets) == data


def test_packet_sequence():
    data = bytes(range(100))

    packets = packetize(
        data,
        session_id=1,
        block_size=20,
    )

    assert [packet.sequence for packet in packets] == [
        0, 1, 2, 3, 4
    ]


def test_last_packet_can_be_smaller():
    data = b"A" * 100

    packets = packetize(
        data,
        session_id=1,
        block_size=32,
    )

    assert [len(packet.payload) for packet in packets] == [
        32, 32, 32, 4
    ]


def test_empty_data():
    packets = packetize(
        b"",
        session_id=1,
        block_size=32,
    )

    assert packets == []
    assert reassemble(packets) == b""


def test_duplicate_sequence_fails():
    data = b"hello world"

    packets = packetize(
        data,
        session_id=1,
        block_size=5,
    )

    packets.append(packets[0])

    with pytest.raises(ValueError, match="duplicate"):
        reassemble(packets)


def test_missing_sequence_fails():
    data = b"A" * 100

    packets = packetize(
        data,
        session_id=1,
        block_size=20,
    )

    packets.pop(2)

    with pytest.raises(ValueError, match="incomplete"):
        reassemble(packets)


def test_mixed_sessions_fail():
    packets = packetize(
        b"hello",
        session_id=1,
        block_size=2,
    )

    packets.append(
        packetize(
            b"world",
            session_id=2,
            block_size=2,
        )[0]
    )

    with pytest.raises(ValueError, match="different sessions"):
        reassemble(packets)

def test_split_into_blocks_pads_final_block() -> None:
    data = b"ABCDEFGHIJ"

    blocks = split_into_blocks(
        data,
        block_size=4,
    )

    assert blocks == [
        b"ABCD",
        b"EFGH",
        b"IJ\x00\x00",
    ]
