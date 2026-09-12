from qr_txrx.application.file_transfer import packetize
from qr_txrx.transport.sequential import (
    SequentialReceiver,
    SequentialSender,
)


def test_sender_preserves_packet_order():
    packets = packetize(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        session_id=1,
        block_size=5,
    )

    sender = SequentialSender(packets)

    transmitted = list(sender.frames())

    assert transmitted == packets


def test_receiver_accepts_packets_out_of_order():
    packets = packetize(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        session_id=1,
        block_size=5,
    )

    receiver = SequentialReceiver()

    for packet in reversed(packets):
        receiver.receive(packet)

    assert receiver.packets() == packets


def test_receiver_counts_packets():
    packets = packetize(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        session_id=1,
        block_size=5,
    )

    receiver = SequentialReceiver()

    for packet in packets:
        receiver.receive(packet)

    assert receiver.packet_count == len(packets)


def test_duplicate_packet_is_rejected():
    packets = packetize(
        b"hello world",
        session_id=1,
        block_size=5,
    )

    receiver = SequentialReceiver()

    receiver.receive(packets[0])

    try:
        receiver.receive(packets[0])
        assert False, "Expected duplicate packet error"
    except ValueError as exc:
        assert "duplicate" in str(exc)
