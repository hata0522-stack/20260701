from abc import ABC, abstractmethod
from typing import Dict, Any
from playwright.async_api import BrowserContext, Page
from models.data_models import StoreInfo
import re

class BasePlatform(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def fetch(self, context: BrowserContext, keyword: str) -> StoreInfo:
        pass

    def clean_price(self, price_text: str) -> int:
        digits = re.sub(r"[^\d]", "", price_text)
        return int(digits) if digits else 0
