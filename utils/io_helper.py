import json
import os
from datetime import datetime
from typing import List, Dict, Any

@dataclass
class AppConfig:
    project_name: str
    version: str
    platforms: List[Dict[str, str]]
    monitor_products: List[Dict[str, Any]]

def load_config(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到設定檔：{file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_report(file_path: str, data: Dict[str, Any]):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_markdown_report(file_path: str, category_scans: List[Any], platforms_names: List[str], elapsed: float):
    # 這裡之後會根據實際的類別物件來實作，先留空或寫簡單邏輯
    pass
