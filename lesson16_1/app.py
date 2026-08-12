"""毛寶競品智能分析儀 —— PySide6 圖形介面。

介面層只負責顯示，抓取邏輯完全重用 scraper.py / *_platform.py。

執行緒模型：
    QThread 內跑自己的 asyncio event loop 執行 Playwright，
    結果以 Signal 送回主執行緒後才建立 QWidget
    —— Qt 規定所有 UI 元件都必須在主執行緒建立。
"""

import asyncio
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig, CategoryConfig
from data_models import StoreInfo
from scraper import PriceScraper, browser_context

# --- 1. 資料來源 ---
# 監控清單唯一資料來源，與 CLI 版 (clawler.py) 共用同一份組態檔
CONFIG_FILE = Path(__file__).resolve().parent / "products_config.json"
SELF_LABEL = "我自己"

# --- 樣式常數 ---
COLOR_PRIMARY = "#007AFF"
COLOR_PRICE = "#E63946"
COLOR_MUTED = "#6C757D"
COLOR_BORDER = "#E9ECEF"


# --- 2. 自定義組件: 商品卡片 ---
class ProductCard(QFrame):
    """顯示單一商品的精美卡片組件"""

    def __init__(self, brand_name: str, info: StoreInfo):
        super().__init__()
        self.setFixedSize(280, 150)
        self.setObjectName("ProductCard")
        self.setStyleSheet(
            "#ProductCard { background-color: white; border-radius: 15px; }"
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        brand_label = QLabel(brand_name)
        brand_label.setStyleSheet(
            f"color: {COLOR_PRIMARY}; font-size: 12px; font-weight: bold;"
        )

        title_label = QLabel(info.title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #212529; font-size: 14px; font-weight: 600;")

        price_label = QLabel(f"${info.price:,}")
        price_label.setStyleSheet(
            f"color: {COLOR_PRICE}; font-size: 20px; font-weight: bold;"
        )

        platform_label = QLabel(info.platform)
        platform_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11px;")

        layout.addWidget(brand_label)
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(price_label)
        layout.addWidget(platform_label)


# --- 3. 非同步工作執行緒 (Scraper Engine) ---
class ScraperWorker(QThread):
    """在背景執行緒中驅動 Playwright，透過 Signal 回報進度與結果。"""

    log_signal = Signal(str)
    progress_signal = Signal(float)
    result_signal = Signal(str, object)  # (顯示標籤, StoreInfo)
    scan_finished = Signal()

    SEARCH_PROGRESS_RATIO = 0.8  # 搜尋階段佔進度條的比例

    def __init__(self, category: CategoryConfig):
        super().__init__()
        self.category = category

    def run(self) -> None:
        asyncio.run(self._execute())

    async def _execute(self) -> None:
        # 搜尋目標與關鍵字全部來自組態檔，自家商品排第一
        targets = self.category.targets

        scraper = PriceScraper(log=self.log_signal.emit)
        try:
            self.log_signal.emit("🚀 初始化瀏覽器環境...")
            async with browser_context(browser_name="chromium", headless=True) as context:
                self.log_signal.emit("📦 啟動抓取引擎...")

                for idx, target in enumerate(targets):
                    label = SELF_LABEL if idx == 0 else target.brand
                    self.progress_signal.emit(idx / len(targets) * self.SEARCH_PROGRESS_RATIO)
                    self.log_signal.emit(f"🔍 正在搜尋 [{label}] 的價格...")

                    info = await scraper.find_first(context, target.keyword)
                    if info:
                        self.result_signal.emit(label, info)
                    else:
                        self.log_signal.emit(f"⚠️ {label}: 無法找到價格資訊 (所有平台皆無結果)")

                    await asyncio.sleep(0.5)

            self.progress_signal.emit(1.0)
            self.log_signal.emit("✅ 任務完成！")
        except Exception as exc:
            self.log_signal.emit(f"❌ 執行過程發生錯誤: {exc}")
        finally:
            # 不論成功或失敗，都要讓介面恢復可操作狀態
            self.scan_finished.emit()


# --- 4. 主程式視窗 ---
class MaobaoDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("毛寶競品智能分析儀")
        self.resize(1050, 750)
        self.worker: ScraperWorker | None = None
        self.config: AppConfig | None = None
        self.setup_ui()
        self.load_config()

    # ---------- 介面組裝 ----------
    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._build_sidebar())
        main_layout.addWidget(self._build_dashboard())

    def _build_sidebar(self) -> QWidget:
        """左側控制面板"""
        panel = QWidget()
        panel.setFixedWidth(320)
        panel.setStyleSheet(f"background-color: white; border-right: 1px solid {COLOR_BORDER};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 40, 25, 30)
        layout.setSpacing(15)

        title = QLabel("毛寶競品分析")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        subtitle = QLabel("選擇產品以啟動自動化抓取流程")
        subtitle.setStyleSheet(f"font-size: 13px; color: {COLOR_MUTED};")
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        layout.addWidget(QLabel("📍 目標產品:"))
        self.product_selector = QComboBox()  # 選項於 load_config() 中填入
        self.product_selector.setStyleSheet(
            "QComboBox { border: 1px solid #CED4DA; border-radius: 8px; padding: 8px; }"
        )
        layout.addWidget(self.product_selector)

        self.search_btn = QPushButton("🚀 開始搜尋競爭者")
        self.search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {COLOR_PRIMARY}; color: white;
                           font-weight: bold; border-radius: 8px; padding: 15px; }}
            QPushButton:hover {{ background-color: #005BB7; }}
            QPushButton:disabled {{ background-color: #CED4DA; }}
        """)
        self.search_btn.clicked.connect(self.start_analysis)
        layout.addWidget(self.search_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            "QProgressBar { height: 8px; border-radius: 4px; }"
            f"QProgressBar::chunk {{ background-color: {COLOR_PRIMARY}; }}"
        )
        layout.addWidget(self.progress_bar)

        layout.addSpacing(10)
        layout.addWidget(QLabel("📋 操作日誌:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            f"background-color: #F8F9FA; border: 1px solid {COLOR_BORDER}; font-size: 11px;"
        )
        layout.addWidget(self.log_view)

        return panel

    def _build_dashboard(self) -> QWidget:
        """右側卡片展示區"""
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setSpacing(20)
        self.card_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self.card_container)
        layout.addWidget(scroll)
        return area

    # ---------- 組態載入 ----------
    def load_config(self) -> None:
        """從 products_config.json 載入監控清單；失敗時停用查詢功能並提示。"""
        try:
            self.config = AppConfig.load(CONFIG_FILE)
        except (OSError, KeyError, ValueError) as exc:
            self.search_btn.setEnabled(False)
            self.update_log(f"❌ 組態檔載入失敗: {exc}")
            QMessageBox.critical(self, "組態檔載入失敗", f"{CONFIG_FILE}\n\n{exc}")
            return

        for category in self.config.categories:
            # 下拉選單顯示商品全名，實際搜尋用的組態存在 userData
            self.product_selector.addItem(category.maobao_product.name, userData=category)

        self.update_log(f"📦 已載入 {len(self.config.categories)} 項監控產品")

    # ---------- 事件處理 ----------
    def start_analysis(self) -> None:
        category: CategoryConfig | None = self.product_selector.currentData()
        if category is None:
            return

        self._reset_ui()

        self.worker = ScraperWorker(category)
        self.worker.log_signal.connect(self.update_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.result_signal.connect(self.add_result_card)
        self.worker.scan_finished.connect(self.on_finished)
        self.worker.start()

    def _reset_ui(self) -> None:
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.log_view.clear()
        self.progress_bar.setValue(0)
        self.search_btn.setEnabled(False)
        self.product_selector.setEnabled(False)

    def update_log(self, msg: str) -> None:
        self.log_view.append(msg)

    def update_progress(self, val: float) -> None:
        self.progress_bar.setValue(int(val * 100))

    def add_result_card(self, label: str, info: StoreInfo) -> None:
        """在主執行緒建立卡片（QWidget 不可在背景執行緒建立）"""
        self.card_layout.addWidget(ProductCard(label, info))

    def on_finished(self) -> None:
        self.search_btn.setEnabled(True)
        self.product_selector.setEnabled(True)

    def closeEvent(self, event) -> None:
        """關閉視窗時等待背景執行緒收尾，避免 Qt 警告與資源殘留"""
        if self.worker and self.worker.isRunning():
            self.worker.wait(5000)
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MaobaoDashboard()
    window.show()
    sys.exit(app.exec())
