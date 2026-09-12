
# QR TXRX

**QR TXRX** is an experimental screen-to-camera optical data transfer system. It combines packetized file transfer, QR visual encoding, CRC-based integrity, and fountain-coded erasure recovery.

The implementation is structured so that the **visual codec**, **transport**, **FEC**, and **channel model** are independent components. This allows the same transport stack to be evaluated with different visual encodings and channel conditions.

## Architecture

```text
                        ┌───────────────┐
                        │     File      │
                        └───────┬───────┘
                                │
                         Packetization
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
           Sequential Transport        Fountain Coding
                  │                           │
                  └─────────────┬─────────────┘
                                │
                           QR Codec
                                │
                         Display / Channel
                                │
                           QR Decoder
                                │
                       Packet / FEC Recovery
                                │
                         File Reconstruction
                                │
                           SHA-256 Check
```

## Repository Structure

```text
qr-txrx/
├── src/qr_txrx/
│   ├── application/
│   │   └── file_transfer.py
│   ├── transport/
│   │   ├── packet.py
│   │   └── sequential.py
│   ├── fec/
│   │   ├── fountain.py
│   │   └── droplet.py
│   ├── codecs/
│   │   └── qr/
│   │       └── codec.py
│   ├── channel/
│   │   └── model.py
│   ├── receiver/
│   ├── benchmark/
│   │   └── metrics.py
│   └── utils/
│       └── integrity.py
└── tests/
    ├── unit/
    ├── integration/
    └── channel/
```

## Protocol

### Packet

Packets use a fixed header followed by a variable-length payload and CRC32:

```text
Offset   Size       Field
────────────────────────────────
0        4          Magic ("QTX1")
4        1          Version
5        4          Session ID
9        4          Sequence Number
13       2          Payload Length
15       N          Payload
15+N     4          CRC32
```

CRC32 covers the header and payload. Decoding validates the magic, version, packet length, and checksum.

Files are packetized into **512-byte payload blocks** by default.

### Sequential Transport

The baseline transport transmits packets in sequence:

```text
P0 → P1 → P2 → P3 → ...
```

The receiver stores packets by sequence number and requires a complete sequence for reconstruction.

### Fountain Transport

The FEC implementation uses XOR-coded droplets over fixed-size source blocks.

```text
D0 = S0
D1 = S0 ⊕ S1
D2 = S1 ⊕ S2
D3 = S0 ⊕ S2 ⊕ S3
```

The decoder solves the resulting GF(2) system using Gaussian elimination, allowing reconstruction without receiving every original source block.

The current degree distribution is intentionally simple and experimental. It is not an implementation of a standardized LT or Raptor code.

### Droplet Format

```text
4 B       Generation ID
4 B       Droplet ID
4 B       Seed
1 B       Degree
4 B × D   Source block indices
N B       Payload
```

Droplet serialization is handled separately from the fountain encoder/decoder.

## QR Codec

The current visual layer uses:

- `qrcode` for QR generation
- `pyzbar` / ZBar for decoding
- Base64 for binary-safe QR payloads

```text
Binary Payload
      │
    Base64
      │
   QR Frame
```

Base64 provides a simple binary-safe baseline at the cost of approximately 33% payload expansion.

The codec is isolated from the transport layer so that alternative 2D encodings can be introduced without changing the underlying protocol.

## Channel Model

A synthetic erasure channel is currently used to evaluate frame loss before introducing a physical camera channel.

```python
ErasureChannel(
    loss_rate=0.20,
    seed=42,
)
```

The model supports deterministic experiments through seeded random loss.

## Integrity

Integrity is checked at two levels:

| Layer | Mechanism | Purpose |
|---|---|---|
| Packet | CRC32 | Detect corrupted packets |
| File | SHA-256 | Verify reconstructed file |

## Tests

The current test suite contains **43 tests** covering packet handling, file transfer, QR encoding/decoding, sequential transport, fountain coding, droplet serialization, erasure channels, and end-to-end QR/FEC transfer.

```bash
pytest -q
```

Current status:

```text
43 passed
```

## Installation

```bash
git clone https://github.com/Tin-card/qr-txrx.git
cd qr-txrx

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
pytest -q
```

## Next Step

The next implementation stage is the **physical display-to-camera channel**, followed by integration and benchmarking of a higher-density 2D codec.


## Repository

[QR TXRX on GitHub](https://github.com/Tin-card/qr-txrx?utm_source=chatgpt.com)

## License

Educational and experimental project.
MIT License
