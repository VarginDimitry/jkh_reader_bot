import json
import logging

from google import genai
from google.genai.errors import ClientError
from google.genai.types import GenerateContentConfig
from PIL import Image

from config import Settings
from schemas import IMPORTANT_COLUMNS, UtilityBillTable
from services.base_table_processor_service import BaseTableProcessorService

# Constrain model output to UtilityBillTable (Gemini structured output / JSON mode).
_GENERATE_TABLE_CONFIG = GenerateContentConfig(
    response_mime_type="application/json",
    response_json_schema=UtilityBillTable.model_json_schema(),
)


class GeminiTableProcessorService(BaseTableProcessorService):
    GEMINI_MODELS_GENERATING: tuple[str, ...] = (
        # "gemini-3-pro-image",
        "gemini-2.5-flash-image",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    )
    MODELS_WITH_LEVELS: tuple[tuple[str, int], ...] = tuple(
        enumerate(GEMINI_MODELS_GENERATING)
    )

    def __init__(self, settings: Settings, logger: logging.Logger, gpt: genai.Client):
        self._settings = settings
        self._logger = logger
        self._gpt = gpt

    async def process_table(self, img_path: str) -> tuple[UtilityBillTable, dict]:
        self._logger.info(f"Processing table from {img_path}")
        model_result, model_info = await self._feed_model(img_path)
        self._logger.info(f"Model result ({model_info=}):\n{model_result}")
        return self._parse_model_result(model_result), {
            "model_name": model_info[0],
            "level": model_info[1],
        }

    async def _feed_model(
        self, img_path: str
    ) -> tuple[str, tuple[str, int]] | tuple[None, None]:
        image = self._preprocess_image(img_path)
        for level, model_name in self.MODELS_WITH_LEVELS:
            try:
                response = await self._gpt.aio.models.generate_content(
                    model=model_name,
                    contents=[PROMPT, image],
                    config=_GENERATE_TABLE_CONFIG,
                )
                return response.text, (model_name, level)
            except ClientError as e:
                if e.code == 429:  # RESOURCE_EXHAUSTED
                    self._logger.error(f"Модель {model_name=} исчерпала квоту")
                else:
                    self._logger.error(
                        f"Ошибка при использовании модели {model_name=} {type(e)=}: {str(e)}"
                    )
                continue
            except Exception as e:
                self._logger.error(
                    f"Ошибка при использовании модели {model_name=} {type(e)=}: {str(e)}"
                )
                continue
        self._logger.error("Все модели исчерпали квоту")
        return None, None

    def _parse_model_result(self, model_result: str) -> UtilityBillTable:
        text = model_result
        if "```json" in text:
            start, end = text.find("```json"), text.rfind("```")
            text = text[start:end].replace("```json", "").replace("```", "")
            self._logger.info(f"Model filtered result: {text}")
        try:
            data = json.loads(text)
            return UtilityBillTable.model_validate(data)
        except Exception:
            raise

    def _preprocess_image(self, img_path: str) -> Image:
        image = Image.open(img_path).convert("RGB")
        return image


PROMPT = """
Table recognition:
You read the table of the Russian utility bill and you should return it as a json strongly.
No markdown, no prose, no code fences.
Return ONLY a valid JSON object with "rows" and "totals" as in the example.
There is the example in config.
Also there are column names that u should detect and dont change my names:
""" + "\n".join(IMPORTANT_COLUMNS)
