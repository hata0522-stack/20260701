"""組態載入層：把 products_config.json 轉成型別明確的物件。

組態驅動設計 (Configuration-Driven)：要監控哪些品類、哪些競品，
全部寫在 JSON 裡，程式碼不需要修改。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union

from data_models import ProductTarget

MAOBAO_BRAND = "毛寶"


@dataclass
class CategoryConfig:
    """單一監控品類：毛寶本家商品 + 多個競品"""
    id: str
    category: str
    maobao_product: ProductTarget
    competitors: List[ProductTarget] = field(default_factory=list)

    @property
    def targets(self) -> List[ProductTarget]:
        """本品類要搜尋的所有目標（毛寶排第一）"""
        return [self.maobao_product] + self.competitors

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "CategoryConfig":
        maobao = raw["maobao_product"]
        return cls(
            id=raw.get("id", ""),
            category=raw["category"],
            maobao_product=ProductTarget(
                # 自家商品預設掛「毛寶」，子品牌（如小鹿山丘）可在組態中覆寫
                brand=maobao.get("brand", MAOBAO_BRAND),
                name=maobao["name"],
                keyword=maobao["keyword"],
            ),
            competitors=[
                ProductTarget(brand=c["brand"], name=c["name"], keyword=c["keyword"])
                for c in raw.get("competitors", [])
            ],
        )


@dataclass
class AppConfig:
    """整份組態檔"""
    project_name: str
    version: str
    platform_names: List[str]
    categories: List[CategoryConfig]

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "AppConfig":
        return cls(
            project_name=raw.get("project_name", ""),
            version=raw.get("version", ""),
            platform_names=[p["name"] for p in raw.get("platforms", [])],
            categories=[
                CategoryConfig.from_dict(item)
                for item in raw.get("monitor_products", [])
            ],
        )

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "AppConfig":
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"找不到設定檔：{path}")
        with path.open("r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
