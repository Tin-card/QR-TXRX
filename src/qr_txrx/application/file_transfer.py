from qr_txrx.transport.packet import Packet


DEFAULT_BLOCK_SIZE = 512


def packetize(
    data: bytes,
    session_id: int,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> list[Packet]:
    """Split data into sequential packets."""

    if block_size <= 0:
        raise ValueError("block_size must be greater than zero")

    return [
        Packet(
            session_id=session_id,
            sequence=sequence,
            payload=data[offset : offset + block_size],
        )
        for sequence, offset in enumerate(range(0, len(data), block_size))
    ]


def split_into_blocks(
    data: bytes,
    block_size: int,
) -> list[bytes]:
    """Split data into equal-sized blocks, padding the final block."""

    if block_size <= 0:
        raise ValueError("block_size must be greater than zero")

    if not data:
        return []

    blocks = [
        data[offset : offset + block_size]
        for offset in range(0, len(data), block_size)
    ]

    if len(blocks[-1]) < block_size:
        blocks[-1] = blocks[-1].ljust(
            block_size,
            b"\x00",
        )

    return blocks

def reassemble(packets: list[Packet]) -> bytes:
    """Reconstruct the original data from sequential packets."""

    if not packets:
        return b""

    session_id = packets[0].session_id

    for packet in packets:
        if packet.session_id != session_id:
            raise ValueError("packets belong to different sessions")

    packets_by_sequence = {}

    for packet in packets:
        if packet.sequence in packets_by_sequence:
            raise ValueError(
                f"duplicate packet sequence: {packet.sequence}"
            )

        packets_by_sequence[packet.sequence] = packet

    sequences = sorted(packets_by_sequence)

    expected_sequences = list(range(len(sequences)))

    if sequences != expected_sequences:
        raise ValueError("packet sequence is incomplete")

    return b"".join(
        packets_by_sequence[sequence].payload
        for sequence in sequences
    )
