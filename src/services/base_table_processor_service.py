from abc import ABC, abstractmethod

from schemas import UtilityBillTable


class BaseTableProcessorService(ABC):
    @abstractmethod
    async def process_table(self, img_path: str) -> tuple[UtilityBillTable, dict]:
        pass
