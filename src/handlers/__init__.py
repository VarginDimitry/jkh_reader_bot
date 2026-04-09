from aiogram import Router

from .echo import echo_router
from .photo import photo_router


def get_router() -> Router:
    router = Router()
    router.include_router(echo_router)
    router.include_router(photo_router)
    return router
