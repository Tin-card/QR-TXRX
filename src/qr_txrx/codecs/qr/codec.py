from base64 import b64decode, b64encode
from io import BytesIO

import cv2
import numpy as np
import qrcode
from PIL import Image


class QRDecodeError(ValueError):
    """Raised when a QR frame cannot be decoded."""


class QRCodec:
    """Encode and decode binary payloads using QR codes."""

    def __init__(
        self,
        box_size: int = 10,
        border: int = 4,
    ) -> None:
        self.box_size = box_size
        self.border = border

    def encode(self, payload: bytes) -> Image.Image:
        """Encode arbitrary bytes into a QR image."""

        encoded = b64encode(payload).decode("ascii")

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
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
        """Decode a QR image back into arbitrary bytes."""

        image_array = np.array(image)

        detector = cv2.QRCodeDetector()

        data, _, _ = detector.detectAndDecode(image_array)

        if not data:
            raise QRDecodeError("QR code could not be decoded")

        try:
            return b64decode(data.encode("ascii"), validate=True)
        except Exception as exc:
            raise QRDecodeError(
                "QR payload is not valid Base64"
            ) from exc
