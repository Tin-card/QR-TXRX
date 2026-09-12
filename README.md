
# QR TXRX

**QR TXRX** is an experimental screen-to-camera optical data transfer system. It combines packetized file transfer, QR visual encoding, CRC-based integrity, and fountain-coded erasure recovery.

The architecture separates the **visual codec** from the **transport/FEC layer**, allowing different 2D visual codecs to be evaluated without changing the communication stack.

## Architecture

```text
File
 │
 ▼
Packetization
 │
 ├───────────────┐
 ▼               ▼
Sequential     Fountain
Transport        FEC
 │               │
 └───────┬───────┘
         ▼
     QR Codec
         │
         ▼
 Display / Channel
         │
         ▼
      Receiver
         │
         ▼
 File Reconstruction
         │
         ▼
    SHA-256 Verify
```

### Repository Structure

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

## Implementation

### 1. Packet Format

Binary packets use the following wire format:

```text
4 B   Magic          QTX1
1 B   Version
4 B   Session ID
4 B   Sequence Number
2 B   Payload Length
N B   Payload
4 B   CRC32
```

CRC32 covers the header and payload. Packets are rejected if their magic, version, length, or CRC is invalid.

### 2. File Packetization

Files are split into sequential **512-byte blocks** by default.

```text
File → Packet 0 → Packet 1 → Packet 2 → ...
```

The receiver verifies session consistency, rejects duplicate packets, checks sequence completeness, and reassembles the original byte stream.

### 3. QR Codec

The current codec uses:

- `qrcode` for encoding
- `pyzbar` / ZBar for decoding
- Base64 for binary-safe QR payload representation

```text
Binary Packet
     ↓
   Base64
     ↓
  QR Image
```

Base64 is currently a baseline representation and introduces approximately 33% data expansion.

### 4. Sequential Transport

The baseline transport sends packets in order:

```text
P0 → P1 → P2 → P3 → ...
```

Loss of a required packet prevents complete sequential reconstruction.

### 5. Fountain Coding

The project implements a simple **XOR fountain code**.

A droplet is generated as the XOR of selected source blocks:

```text
D0 = S0
D1 = S0 ⊕ S1
D2 = S1 ⊕ S2
D3 = S0 ⊕ S2 ⊕ S3
```

The decoder uses **GF(2) Gaussian elimination** to reconstruct the source blocks from received droplets.

The current degree distribution is a simple experimental distribution, not a production LT/Raptor implementation.

### 6. Droplet Format

```text
4 B       Generation ID
4 B       Droplet ID
4 B       Seed
1 B       Degree
4 B × D   Source Block Indices
N B       Payload
```

The droplet layer validates degree, truncation, payload size, and duplicate indices. `FountainDecoder` additionally validates source-block indices.

### 7. Synthetic Channel

Frame loss can be simulated using a configurable erasure channel:

```text
loss_rate = 0.0   → no loss
loss_rate = 0.2   → 20% loss
loss_rate = 1.0   → complete loss
```

A random seed allows reproducible experiments.

### 8. Integrity

Two levels of integrity checking are used:

- **CRC32** → individual packet validation
- **SHA-256** → final reconstructed-file verification

## Testing

The implementation currently has **43 passing tests** covering:

- Packet serialization and validation
- File packetization/reassembly
- QR encoding/decoding
- Sequential transport
- Fountain encoding/decoding
- Droplet serialization
- Erasure-channel behavior
- QR + sequential integration
- QR + fountain integration
- End-to-end SHA-256 verification

Run:

```bash
pytest -q
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

## Current Next Step

The next major step is to move from the synthetic QR/erasure pipeline toward the **physical display → camera channel**, followed by evaluation of a higher-density 2D codec such as HCC2D.

## Repository

[QR TXRX on GitHub](https://github.com/Tin-card/qr-txrx?utm_source=chatgpt.com)

## License

Educational and experimental project.
MIT License
