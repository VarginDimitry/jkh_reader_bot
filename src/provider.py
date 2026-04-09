import logging
import sys

from aiogram import Bot
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from google.genai import Client

from config import Settings
from services.base_table_processor_service import BaseTableProcessorService
from services.gemini_table_processor_service import GeminiTableProcessorService

# from transformers import AutoModelForImageTextToText, AutoProcessor


class RootProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return Settings()

    @provide(scope=Scope.APP)
    def provide_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        return logger

    @provide(scope=Scope.APP)
    def provide_gemini(self, settings: Settings) -> Client:
        return Client(api_key=settings.gemini_api_key)

    @provide(scope=Scope.APP)
    def provide_table_processor_service(
        self,
        settings: Settings,
        logger: logging.Logger,
        gpt: Client,
    ) -> BaseTableProcessorService:
        return GeminiTableProcessorService(
            settings=settings,
            logger=logger,
            gpt=gpt,
        )

    @provide(scope=Scope.APP)
    def provide_bot(self, settings: Settings) -> Bot:
        return Bot(token=settings.bot_token)


def build_container() -> AsyncContainer:
    return make_async_container(RootProvider())
