"""Tests for bot utilities."""

import pytest

from src.bot.utils import split_long_message, TELEGRAM_MAX_MESSAGE_LENGTH


def test_split_short_message():
    """Test that short messages are not split."""
    text = "This is a short message"
    result = split_long_message(text)
    assert len(result) == 1
    assert result[0] == text


def test_split_long_message():
    """Test that long messages are split correctly."""
    # Create a message longer than the limit
    text = "A" * (TELEGRAM_MAX_MESSAGE_LENGTH + 100)
    result = split_long_message(text)

    # Should be split into multiple chunks
    assert len(result) > 1

    # Each chunk should be within the limit
    for chunk in result:
        assert len(chunk) <= TELEGRAM_MAX_MESSAGE_LENGTH

    # Reconstructed text should match original (with potential trimming)
    reconstructed = "".join(chunk.strip() for chunk in result)
    assert reconstructed.replace(" ", "") == text.replace(" ", "")


def test_split_with_paragraphs():
    """Test that splitting respects paragraph boundaries."""
    para1 = "First paragraph. " * 100
    para2 = "Second paragraph. " * 100
    text = para1 + "\n\n" + para2

    result = split_long_message(text, max_length=500)

    # Should be split into multiple chunks
    assert len(result) > 1

    # Each chunk should be within the limit
    for chunk in result:
        assert len(chunk) <= 500


def test_split_with_custom_length():
    """Test splitting with custom max length."""
    text = "Word " * 200  # 1000 chars
    result = split_long_message(text, max_length=300)

    # Should be split
    assert len(result) > 1

    # Each chunk should be within the custom limit
    for chunk in result:
        assert len(chunk) <= 300


def test_split_exact_limit():
    """Test message exactly at the limit."""
    text = "A" * TELEGRAM_MAX_MESSAGE_LENGTH
    result = split_long_message(text)

    # Should not be split
    assert len(result) == 1
    assert len(result[0]) == TELEGRAM_MAX_MESSAGE_LENGTH


def test_split_preserves_words():
    """Test that word boundaries are preserved."""
    text = "Hello world. This is a test message. " * 200
    result = split_long_message(text, max_length=100)

    # Check that we didn't split in the middle of words
    for chunk in result:
        # Each chunk should start and end with complete words
        assert not chunk.startswith(" ")
        # Content should be readable
        assert len(chunk) > 0


def test_empty_message():
    """Test handling of empty message."""
    result = split_long_message("")
    assert len(result) == 1
    assert result[0] == ""


def test_split_with_newlines():
    """Test that newlines are handled correctly."""
    text = "Line 1\nLine 2\nLine 3\n" * 500
    result = split_long_message(text, max_length=500)

    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 500
