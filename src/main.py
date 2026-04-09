import asyncio

from aiogram import Bot, Dispatcher
from dishka.integrations.aiogram import setup_dishka

from config import Settings
from handlers import get_router
from middleware.allowed_users import AllowedUsersMiddleware
from provider import build_container


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(get_router())
    container = build_container()
    settings = await container.get(Settings)
    if settings.allowed_telegram_user_ids:
        user_filter = AllowedUsersMiddleware(settings.allowed_telegram_user_ids)
        dp.message.middleware(user_filter)
        dp.edited_message.middleware(user_filter)
        dp.callback_query.middleware(user_filter)
    setup_dishka(
        container=container,
        router=dp,
        auto_inject=True,
    )
    bot = await container.get(Bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
