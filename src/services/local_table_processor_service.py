import json
import logging

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

from config import OrcModels, Settings
from services.base_table_processor_service import BaseTableProcessorService


class LocalTableProcessorService(BaseTableProcessorService):
    def __init__(
        self,
        settings: Settings,
        logger: logging.Logger,
        model: AutoModelForImageTextToText,
        processor: AutoProcessor,
    ):
        self._settings = settings
        self._logger = logger
        self._model = model
        self._processor = processor

    async def process_table(self, img_path: str) -> dict:
        self._logger.info(f"Processing table from {img_path}")
        model_result = self._feed_model(img_path)
        self._logger.info(f"Model result: {model_result}")
        return self._parse_model_result(model_result)

    def _feed_model(self, img_path: str) -> dict:
        max_new_tokens = 2**10
        inputs = self._get_inputs(self._preprocess_image(img_path), max_new_tokens)
        with torch.inference_mode():
            outputs = self._model.generate(
                **inputs, max_new_tokens=max_new_tokens, do_sample=False, use_cache=True
            )
        if self._settings.orc_model == OrcModels.BIG:
            output_text = self._processor.decode(
                outputs[0][inputs["input_ids"].shape[1] :],
                skip_special_tokens=False,
            )
        elif self._settings.orc_model == OrcModels.MINI:
            output_text = self._processor.decode(
                outputs[0][inputs["input_ids"].shape[-1] :]
            )
        else:
            raise ValueError(f"Invalid ORC model: {self._settings.orc_model}")
        return output_text

    def _parse_model_result(self, model_result: str) -> dict:
        start, end = model_result.find("```json"), model_result.rfind("```")
        model_result = model_result[start:end].replace("```json", "").replace("```", "")
        self._logger.info(f"Model filtered result: {model_result}")
        try:
            return json.loads(model_result)
        except Exception:
            raise

    def _preprocess_image(self, img_path: str) -> Image:
        image = Image.open(img_path).convert("RGB")
        return image

    def _get_inputs(self, image: Image, max_new_tokens: int) -> dict:
        messages = self._get_messages(image, max_new_tokens)
        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)
        inputs.pop("token_type_ids", None)
        return inputs

    def _get_messages(self, image: Image, max_new_tokens: int) -> list:
        if self._settings.orc_model == OrcModels.BIG:
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": FULL_PROMPT,
                        },
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                    ],
                },
            ]
        elif self._settings.orc_model == OrcModels.MINI:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": "Table Recognition:"},
                    ],
                }
            ]
        else:
            raise ValueError(f"Invalid ORC model: {self._settings.orc_model}")
        return messages


CUT_PROMPT = """
You are extracting structured data from a Russian utility bill image.
For each row:
- take the service name from column "Услуга"
- take the final full cost from the rightmost column "Итого"
Strict rules:
- Return ONLY a valid JSON array.
- No markdown, no prose, no code fences.
- Ignore headers, empty rows, separators, and summary rows such as "ИТОГО".
- Read totals only from "Итого", not from "Начислено" or "Перерасчет".
JSON schema:
[
  {"service": "string", "total": 0.0},
  ...
]
"""

FULL_PROMPT = """
You are extracting structured data from a Russian utility bill image.

Find the main utilities table and extract all service rows.

For each row:
- take the service name from column "Услуга"
- take the final full cost from the rightmost column "Итого"

Strict rules:
- Return ONLY a valid JSON array.
- No markdown, no prose, no code fences.
- Output objects in the same order as rows appear in the table.
- Ignore headers, empty rows, separators, and summary rows such as "ИТОГО".
- Keep service names as written, but normalize repeated spaces.
- If a service name spans multiple lines, merge it into one string.
- Read totals only from "Итого", not from "Начислено" or "Перерасчет".
- Convert numeric values to JSON numbers with decimal point.
- Do not include currency symbols.
- Do not guess unreadable values.

JSON schema:
[
  {"service": "string", "total": 0.0},
  ...
]
"""

MINIMAL_PROMPT = """
Extract rows from the utilities table.

Return JSON array with:
- service from column "Услуга"
- total from column "Итого"

Ignore header and row "ИТОГО".

Format:
[{"service":"name","total":0.0}]
Return JSON only.
"""
