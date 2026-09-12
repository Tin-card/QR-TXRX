import pytest

from qr_txrx.channel.model import ErasureChannel


def test_zero_loss_preserves_all_frames():
    frames = list(range(100))

    channel = ErasureChannel(
        loss_rate=0.0,
        seed=42,
    )

    received = list(channel.transmit(frames))

    assert received == frames


def test_full_loss_discards_all_frames():
    frames = list(range(100))

    channel = ErasureChannel(
        loss_rate=1.0,
        seed=42,
    )

    received = list(channel.transmit(frames))

    assert received == []


def test_invalid_loss_rate():
    with pytest.raises(ValueError):
        ErasureChannel(loss_rate=-0.1)

    with pytest.raises(ValueError):
        ErasureChannel(loss_rate=1.1)


def test_seed_makes_channel_reproducible():
    frames = list(range(100))

    channel_a = ErasureChannel(
        loss_rate=0.3,
        seed=42,
    )

    channel_b = ErasureChannel(
        loss_rate=0.3,
        seed=42,
    )

    received_a = list(channel_a.transmit(frames))
    received_b = list(channel_b.transmit(frames))

    assert received_a == received_b


def test_loss_rate_is_statistically_reasonable():
    frames = list(range(10_000))

    channel = ErasureChannel(
        loss_rate=0.2,
        seed=42,
    )

    received = list(channel.transmit(frames))

    observed_loss = 1 - len(received) / len(frames)

    assert observed_loss == pytest.approx(
        0.2,
        abs=0.02,
    )
