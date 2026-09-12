from collections.abc import Iterable, Iterator

from qr_txrx.transport.packet import Packet


class SequentialSender:
    """Produce packets in sequence for sequential transmission."""

    def __init__(self, packets: Iterable[Packet]) -> None:
        self._packets = list(packets)

    def frames(self) -> Iterator[Packet]:
        """Yield packets in transmission order."""
        yield from self._packets


class SequentialReceiver:
    """Collect packets and reconstruct them in sequence."""

    def __init__(self) -> None:
        self._packets: dict[int, Packet] = {}

    def receive(self, packet: Packet) -> None:
        """Accept one received packet."""

        if packet.sequence in self._packets:
            raise ValueError(
                f"duplicate packet sequence: {packet.sequence}"
            )

        self._packets[packet.sequence] = packet

    @property
    def packet_count(self) -> int:
        """Number of unique packets received."""
        return len(self._packets)

    def packets(self) -> list[Packet]:
        """Return received packets in sequence order."""
        return [
            self._packets[sequence]
            for sequence in sorted(self._packets)
        ]
