from dataclasses import dataclass
import struct
import zlib


MAGIC = b"QTX1"
VERSION = 1

HEADER_FORMAT = "!4sBIIH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
CRC_SIZE = 4


class PacketError(ValueError):
    """Raised when a packet is malformed or corrupted."""


@dataclass(frozen=True)
class Packet:
    session_id: int
    sequence: int
    payload: bytes

    def encode(self) -> bytes:
        """Serialize the packet into its binary wire format."""

        if not 0 <= self.session_id <= 0xFFFFFFFF:
            raise PacketError("session_id must fit in 32 bits")

        if not 0 <= self.sequence <= 0xFFFFFFFF:
            raise PacketError("sequence must fit in 32 bits")

        if len(self.payload) > 0xFFFF:
            raise PacketError("payload exceeds 65535 bytes")

        header = struct.pack(
            HEADER_FORMAT,
            MAGIC,
            VERSION,
            self.session_id,
            self.sequence,
            len(self.payload),
        )

        body = header + self.payload
        crc = zlib.crc32(body) & 0xFFFFFFFF

        return body + struct.pack("!I", crc)

    @classmethod
    def decode(cls, data: bytes) -> "Packet":
        """Deserialize and validate a binary packet."""

        if len(data) < HEADER_SIZE + CRC_SIZE:
            raise PacketError("packet is too short")

        header = data[:HEADER_SIZE]

        magic, version, session_id, sequence, payload_length = struct.unpack(
            HEADER_FORMAT,
            header,
        )

        if magic != MAGIC:
            raise PacketError("invalid packet magic")

        if version != VERSION:
            raise PacketError(f"unsupported packet version: {version}")

        expected_size = HEADER_SIZE + payload_length + CRC_SIZE

        if len(data) != expected_size:
            raise PacketError("packet length does not match payload length")

        body = data[: HEADER_SIZE + payload_length]

        received_crc = struct.unpack(
            "!I",
            data[-CRC_SIZE:],
        )[0]

        calculated_crc = zlib.crc32(body) & 0xFFFFFFFF

        if received_crc != calculated_crc:
            raise PacketError("CRC check failed")

        payload = data[HEADER_SIZE : HEADER_SIZE + payload_length]

        return cls(
            session_id=session_id,
            sequence=sequence,
            payload=payload,
        )
