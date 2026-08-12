"""資料模型：以 dataclass 描述抓取流程中流動的資料結構。

    ProductTarget  → 要搜尋什麼（品牌 / 名稱 / 關鍵字）
    StoreInfo      → 單一賣場抓到的結果
    ProductScan    → 一個品牌在多個賣場的結果
    CategoryScan   → 一個品類（毛寶 + 競品）的完整結果
"""

from dataclasses import dataclass, field
from typing import List

STATUS_SUCCESS = "成功"
STATUS_EMPTY = "無結果"


@dataclass
class ProductTarget:
    """組態檔中的單一搜尋目標"""
    brand: str
    name: str
    keyword: str


@dataclass
class StoreInfo:
    """單一賣場的商品抓取結果"""
    platform: str
    title: str = "未找到相關商品"
    price: int = 0
    url: str = ""
    status: str = STATUS_EMPTY

    @property
    def found(self) -> bool:
        """是否成功抓到「有價格」的商品"""
        return self.status == STATUS_SUCCESS and self.price > 0


@dataclass
class ProductScan:
    """特定品牌的產品掃描結果，包含多個賣場資訊"""
    brand: str
    name: str
    keyword: str
    stores: List[StoreInfo] = field(default_factory=list)

    @classmethod
    def empty(cls, target: ProductTarget) -> "ProductScan":
        """建立一筆沒有任何賣場結果的空白掃描（抓取失敗時使用）"""
        return cls(brand=target.brand, name=target.name, keyword=target.keyword)


@dataclass
class CategoryScan:
    """單一品類的完整掃描結果"""
    category: str
    maobao_product: ProductScan
    competitors: List[ProductScan] = field(default_factory=list)

    @property
    def products(self) -> List[ProductScan]:
        """毛寶本家商品排在第一筆，其後為競品"""
        return [self.maobao_product] + self.competitors
