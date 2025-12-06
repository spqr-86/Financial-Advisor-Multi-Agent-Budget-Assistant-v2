"""Bot handlers."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="main")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}\n\n"
        "Я Budget Assistant v2.0 🚀"
    )

