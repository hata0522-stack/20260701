from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class StoreInfo:
    """單一賣場的商品抓取結果"""
    platform: str
    title: str = "未找到相關商品"
    price: int = 0
    url: str = ""
    status: str = "無結果"

@dataclass
class ProductScan:
    """特定品牌的產品掃描結果，包含多個賣場資訊"""
    brand: str
    name: str
    keyword: str
    stores: List[StoreInfo] = field(default_factory=list)

@dataclass
class CategoryScan:
    """單一品類的完整掃描結果"""
    category: str
    maobao_product: Optional[ProductScan] = None
    competitors: List[ProductScan] = field(default_factory=list)
