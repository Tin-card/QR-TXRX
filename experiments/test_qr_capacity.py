from qr_txrx.codecs.qr.codec import QRCodec


def main():
    codec = QRCodec()

    print("Payload bytes | Image size | Result")
    print("-" * 40)

    for size in range(32, 513, 32):
        payload = bytes(range(256)) * ((size + 255) // 256)
        payload = payload[:size]

        image = codec.encode(payload)

        try:
            decoded = codec.decode(image)

            result = "PASS" if decoded == payload else "WRONG DATA"

        except Exception:
            result = "FAIL"

        print(
            f"{size:13d} | "
            f"{image.width}x{image.height:4d} | "
            f"{result}"
        )


if __name__ == "__main__":
    main()
