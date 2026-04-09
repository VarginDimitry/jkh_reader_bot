from logging import Logger

from aiogram import F, Router
from aiogram.types import Message
from dishka import FromDishka

echo_router = Router()


@echo_router.message(~F.photo)
async def handle_photo_message(
    message: Message,
    logger: FromDishka[Logger],
) -> None:
    await message.answer(f"Echo: {message.text}")
