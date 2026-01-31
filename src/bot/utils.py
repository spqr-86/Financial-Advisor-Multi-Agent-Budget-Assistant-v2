"""Bot utility functions."""

import asyncio
from typing import List

from aiogram.types import InlineKeyboardMarkup, Message

from src.core.constants import MESSAGE_CHUNK_DELAY, TELEGRAM_MAX_MESSAGE_LENGTH


def format_period_display(period: str) -> str:
    """Convert period code to display string.

    Args:
        period: Period code ("week" or "YYYY_MM")

    Returns:
        Human-readable period string in Russian

    Examples:
        >>> format_period_display("week")
        'неделю'
        >>> format_period_display("2026_01")
        'Январь 2026'
    """
    if period == "week":
        return "неделю"
    if "_" in period:
        from src.bot.keyboards.inline import MONTH_NAMES

        year, month = period.split("_")
        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    return period


def split_long_message(text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Split long message into chunks that fit Telegram's message length limit.

    Args:
        text: The message text to split
        max_length: Maximum length per message (default: 4096 for Telegram)

    Returns:
        List of message chunks, each within the max_length limit

    Example:
        >>> text = "A" * 5000
        >>> chunks = split_long_message(text)
        >>> len(chunks)
        2
        >>> all(len(chunk) <= 4096 for chunk in chunks)
        True
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first (double newline)
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        # If single paragraph is too long, split by sentences
        if len(paragraph) > max_length:
            sentences = paragraph.split(". ")
            for sentence in sentences:
                # If single sentence is too long, split by words
                if len(sentence) > max_length:
                    words = sentence.split(" ")
                    for word in words:
                        # If a single word is too long (rare), force split by characters
                        if len(word) > max_length:
                            # Split the word itself into max_length chunks
                            for i in range(0, len(word), max_length):
                                chunk_part = word[i : i + max_length]
                                if len(current_chunk) + len(chunk_part) + 1 > max_length:
                                    if current_chunk:
                                        chunks.append(current_chunk.strip())
                                        current_chunk = ""
                                current_chunk += chunk_part + " "
                        else:
                            if len(current_chunk) + len(word) + 1 > max_length:
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                    current_chunk = ""
                            current_chunk += word + " "
                else:
                    if len(current_chunk) + len(sentence) + 2 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                    current_chunk += sentence + ". "
        else:
            if len(current_chunk) + len(paragraph) + 2 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
            current_chunk += paragraph + "\n\n"

    # Add remaining chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


async def send_chunked_message(
    message: Message,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
) -> None:
    """Send a long message in chunks with optional keyboard on last chunk.

    Args:
        message: The message to reply to
        text: Text to send (will be split if too long)
        keyboard: Optional keyboard to attach to the last chunk
        parse_mode: Parse mode for the message (default: HTML)
    """
    chunks = split_long_message(text)

    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await message.answer(
            chunk,
            parse_mode=parse_mode,
            reply_markup=keyboard if is_last else None,
        )
        if not is_last:
            await asyncio.sleep(MESSAGE_CHUNK_DELAY)
