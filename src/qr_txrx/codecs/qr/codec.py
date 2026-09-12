from __future__ import annotations

import base64

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode


class QRDecodeError(ValueError):
    """Raised when a QR frame cannot be decoded."""


class QRCodec:
    """Encode and decode arbitrary binary payloads using QR codes."""

    def __init__(
        self,
        box_size: int = 10,
        border: int = 4,
        error_correction: int = qrcode.constants.ERROR_CORRECT_L,
    ) -> None:
        self.box_size = box_size
        self.border = border
        self.error_correction = error_correction

    def encode(self, payload: bytes) -> Image.Image:
        """Encode arbitrary binary data into a QR image."""

        encoded = base64.b64encode(payload).decode("ascii")

        qr = qrcode.QRCode(
            version=None,
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )

        qr.add_data(encoded)
        qr.make(fit=True)

        return qr.make_image(
            fill_color="black",
            back_color="white",
        ).convert("RGB")

    def decode(self, image: Image.Image) -> bytes:
        """Decode a QR image into the original binary payload."""

        results = decode(image)

        for result in results:
            if result.type != "QRCODE":
                continue

            try:
                return base64.b64decode(
                    result.data,
                    validate=True,
                )
            except (ValueError, UnicodeEncodeError) as exc:
                raise QRDecodeError(
                    "QR payload is not valid Base64"
                ) from exc

        raise QRDecodeError("QR code could not be decoded")
