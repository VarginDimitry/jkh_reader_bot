from logging import Logger
from typing import cast

from aiofiles.tempfile import NamedTemporaryFile
from aiogram import F, Router
from aiogram.types import Message, PhotoSize
from dishka import FromDishka

from schemas import IMPORTANT_COLUMNS, UtilityBillTable
from services.base_table_processor_service import BaseTableProcessorService

photo_router = Router()


def get_sum_message(table: UtilityBillTable) -> str:
    lines = ""
    total = 0.0
    founded: set[str] = set()
    for row in table.rows:
        if row.service in IMPORTANT_COLUMNS:
            lines += f"{row.service}: {row.total}\n"
            total += row.total
            founded.add(row.service)
    for column in IMPORTANT_COLUMNS - founded:
        lines += f"{column}: not found\n"
    return f"Total: {total}\n\n{lines}"


@photo_router.message(F.photo)
async def handle_photo_message(
    message: Message,
    table_processor_service: FromDishka[BaseTableProcessorService],
    logger: FromDishka[Logger],
) -> None:
    photo = cast(PhotoSize, message.photo[-1])
    logger.info(f"Photo received: {photo.file_id=}")

    tg_file = await message.bot.get_file(photo.file_id)
    async with NamedTemporaryFile("wb") as f:
        # async with aiofiles.open("tg_file.jpg", "wb") as f:
        logger.info(f"Downloading photo to {f.name}")
        await message.bot.download_file(tg_file.file_path, f.name)
        logger.info(f"Photo downloaded to {f.name}")
        result, meta = await table_processor_service.process_table(f.name)
        logger.info(f"Result ({meta=}):\n{result}")
        await message.answer(
            get_sum_message(result)
            + f"\nModel: {meta['model_name']} (level: {meta['level']})",
        )
