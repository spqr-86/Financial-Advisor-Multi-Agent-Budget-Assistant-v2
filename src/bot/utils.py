"""Bot utility functions."""

from typing import List

# Telegram message limit
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


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
