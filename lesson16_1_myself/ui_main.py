"""毛寶企業競品價格監控系統 - PySide6 圖形介面。

使用方式：
    python ui_main.py
"""
import asyncio
import os
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QThread, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

import io_helper
import scanner
from data_models import CategoryScan, StoreInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_CONFIG = os.path.join(BASE_DIR, "products_config.json")
REPORT_JSON = os.path.join(BASE_DIR, "price_report.json")
REPORT_MD = os.path.join(BASE_DIR, "price_report.md")

THEME_QSS = """
QWidget {
    font-family: "Microsoft JhengHei", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #1e293b;
}
QWidget#central {
    background: #eef2f7;
}
QFrame#banner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1e3a8a, stop:1 #4f46e5);
    border-radius: 12px;
}
QLabel#appTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
}
QLabel#appSubtitle {
    color: rgba(255, 255, 255, 0.88);
    font-size: 12px;
}
QLabel#fieldLabel {
    font-weight: 600;
    color: #475569;
}
QPushButton {
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton:hover { background: #f1f5f9; border-color: #94a3b8; }
QPushButton:pressed { background: #e2e8f0; }
QPushButton:disabled { color: #94a3b8; background: #e2e8f0; }
QPushButton#startBtn {
    background: #16a34a; color: #ffffff; border: none; font-weight: 700;
}
QPushButton#startBtn:hover { background: #15803d; }
QPushButton#startBtn:disabled { background: #86efac; }
QPushButton#searchBtn {
    background: #2563eb; color: #ffffff; border: none; font-weight: 700;
}
QPushButton#searchBtn:hover { background: #1d4ed8; }
QPushButton#searchBtn:disabled { background: #93c5fd; }
QPushButton#stopBtn {
    background: #dc2626; color: #ffffff; border: none; font-weight: 700;
}
QPushButton#stopBtn:hover { background: #b91c1c; }
QPushButton#stopBtn:disabled { background: #fca5a5; }
QLineEdit {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px 10px;
}
QLineEdit:focus { border-color: #2563eb; }
QLineEdit:disabled { background: #e2e8f0; }
QGroupBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    margin-top: 10px;
    font-weight: 700;
    color: #334155;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QTreeWidget {
    background: #ffffff;
    border: none;
    outline: none;
}
QTreeWidget::item { padding: 3px 2px; border-radius: 4px; }
QTreeWidget::item:hover { background: #f1f5f9; }
QTreeWidget::item:selected { background: #dbeafe; color: #1e3a8a; }
QTableWidget {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #eef2f7;
}
QTableWidget::item:selected { background: #dbeafe; color: #1e3a8a; }
QHeaderView::section {
    background: #f8fafc;
    color: #334155;
    font-weight: 700;
    padding: 7px;
    border: none;
    border-bottom: 2px solid #cbd5e1;
}
QPlainTextEdit {
    background: #0f172a;
    color: #e2e8f0;
    border: none;
    border-radius: 8px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
}
QStatusBar {
    background: #ffffff;
    color: #475569;
}
QToolTip { background: #1e293b; color: #ffffff; border: none; padding: 4px; }
"""


class CrawlerWorker(QThread):
    """在背景執行緒執行 asyncio 爬蟲，透過 Signals 與主執行緒通訊。"""

    log_ready = Signal(str)
    monitoring_finished = Signal(list, float)
    keyword_finished = Signal(list, float)
    failed = Signal(str)

    def __init__(self, config_data: Dict[str, Any], keyword: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._config_data = config_data
        self._keyword = keyword
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        def log(msg: str) -> None:
            self.log_ready.emit(msg)

        try:
            if self._keyword:
                stores, elapsed = asyncio.run(
                    scanner.run_keyword_scan(self._config_data, self._keyword, log=log)
                )
                self.keyword_finished.emit(stores, elapsed)
            else:
                scans, elapsed = asyncio.run(
                    scanner.run_monitoring(self._config_data, self._stop_event, log=log)
                )
                self.monitoring_finished.emit(scans, elapsed)
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    HEADERS = ["品類", "品牌", "賣場", "商品標題", "售價 (TWD)", "狀態", "商品連結"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("毛寶企業競品價格監控系統")
        self.resize(1240, 800)

        self._config_data: Optional[Dict[str, Any]] = None
        self._platform_names: List[str] = []
        self._worker: Optional[CrawlerWorker] = None
        self._last_scans: List[CategoryScan] = []
        self._last_elapsed: float = 0.0

        self._build_ui()
        self._load_config()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("central")
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # 頂部橫幅
        banner = QFrame()
        banner.setObjectName("banner")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(20, 14, 20, 14)
        title = QLabel("毛寶企業競品價格監控系統")
        title.setObjectName("appTitle")
        subtitle = QLabel("PChome 24h × momo 購物網 × Yahoo 購物中心 — 多賣場平行併發查價")
        subtitle.setObjectName("appSubtitle")
        banner_layout.addWidget(title)
        banner_layout.addWidget(subtitle)
        root.addWidget(banner)

        # 設定檔列
        cfg_row = QHBoxLayout()
        cfg_label = QLabel("設定檔：")
        cfg_label.setObjectName("fieldLabel")
        cfg_row.addWidget(cfg_label)
        self.cfg_edit = QLineEdit(DEFAULT_CONFIG)
        self.cfg_edit.setReadOnly(True)
        cfg_row.addWidget(self.cfg_edit, 1)
        browse_btn = QPushButton("瀏覽")
        browse_btn.clicked.connect(self._browse_config)
        cfg_row.addWidget(browse_btn)
        self.reload_btn = QPushButton("載入設定")
        self.reload_btn.clicked.connect(self._load_config)
        cfg_row.addWidget(self.reload_btn)
        root.addLayout(cfg_row)

        # 操作列
        action_row = QHBoxLayout()
        self.start_btn = QPushButton("▶ 開始監控")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self._start_monitoring)
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("輸入關鍵字即時查價（如：毛寶 冷洗精）")
        self.keyword_edit.returnPressed.connect(self._start_keyword_scan)
        self.search_btn = QPushButton("即時查價")
        self.search_btn.setObjectName("searchBtn")
        self.search_btn.clicked.connect(self._start_keyword_scan)
        self.stop_btn = QPushButton("■ 停止")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self._request_stop)
        self.stop_btn.setEnabled(False)
        self.export_json_btn = QPushButton("匯出 JSON")
        self.export_json_btn.clicked.connect(self._export_json)
        self.export_md_btn = QPushButton("匯出 MD")
        self.export_md_btn.clicked.connect(self._export_md)

        action_row.addWidget(self.start_btn)
        action_row.addWidget(self.keyword_edit, 1)
        action_row.addWidget(self.search_btn)
        action_row.addWidget(self.stop_btn)
        action_row.addWidget(self.export_json_btn)
        action_row.addWidget(self.export_md_btn)
        root.addLayout(action_row)

        # 主區域：左側品類勾選 + 右側表格/日誌
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree_group = QGroupBox("監控品類（勾選要查的產品）")
        tree_layout = QVBoxLayout(self.tree_group)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(280)
        tree_layout.addWidget(self.tree)
        select_row = QHBoxLayout()
        self.select_all_btn = QPushButton("全選")
        self.select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        self.select_none_btn = QPushButton("全不選")
        self.select_none_btn.clicked.connect(lambda: self._set_all_checked(False))
        select_row.addWidget(self.select_all_btn)
        select_row.addWidget(self.select_none_btn)
        select_row.addStretch(1)
        tree_layout.addLayout(select_row)
        main_splitter.addWidget(self.tree_group)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.cellDoubleClicked.connect(self._open_link)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col in (0, 1, 2, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        right_splitter.addWidget(self.table)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        right_splitter.addWidget(self.log_view)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        root.addWidget(main_splitter, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage("就緒")

    # ------------------------------------------------------------ helpers
    def _append_log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{ts}] {msg}")

    def _set_busy(self, busy: bool) -> None:
        self.start_btn.setEnabled(not busy)
        self.search_btn.setEnabled(not busy)
        self.keyword_edit.setEnabled(not busy)
        self.reload_btn.setEnabled(not busy)
        self.tree.setEnabled(not busy)
        self.select_all_btn.setEnabled(not busy)
        self.select_none_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(busy)

    def _add_row(self, category: str, brand: str, store: StoreInfo) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        cells = [
            category,
            brand,
            store.platform,
            store.title,
            f"${store.price}" if store.price > 0 else "未找到",
            store.status,
            store.url,
        ]
        for col, text in enumerate(cells):
            item = QTableWidgetItem(text)
            if col == 5:
                item.setForeground(Qt.GlobalColor.darkGreen if text == "成功" else Qt.GlobalColor.darkRed)
            self.table.setItem(row, col, item)

    def _populate_scans(self, scans: List[CategoryScan]) -> None:
        self.table.setRowCount(0)
        for cat in scans:
            prods = [p for p in ([cat.maobao_product] + cat.competitors) if p is not None]
            for prod in prods:
                for store in prod.stores:
                    self._add_row(cat.category, prod.brand, store)

    def _populate_keyword(self, keyword: str, stores: List[StoreInfo]) -> None:
        self.table.setRowCount(0)
        for store in stores:
            self._add_row(keyword, "-", store)

    def _open_link(self, row: int, col: int) -> None:
        if col != len(self.HEADERS) - 1:
            return
        url = self.table.item(row, col).text()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    # -------------------------------------------------------- 品類勾選
    def _rebuild_category_tree(self, categories: List[Dict[str, Any]]) -> None:
        self.tree.clear()
        for cat in categories:
            cat_item = QTreeWidgetItem([cat["category"]])
            cat_item.setFlags(
                cat_item.flags()
                | Qt.ItemFlag.ItemIsAutoTristate
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            cat_item.setData(0, Qt.ItemDataRole.UserRole, cat)
            self.tree.addTopLevelItem(cat_item)

            mb = cat.get("maobao_product")
            if mb:
                mb_item = QTreeWidgetItem([f"[毛寶] {mb['name']}（{mb['keyword']}）"])
                mb_item.setData(0, Qt.ItemDataRole.UserRole, mb)
                mb_item.setData(0, Qt.ItemDataRole.UserRole + 1, "maobao")
                cat_item.addChild(mb_item)

            for comp in cat.get("competitors", []):
                comp_item = QTreeWidgetItem(
                    [f"[{comp['brand']}] {comp['name']}（{comp['keyword']}）"]
                )
                comp_item.setData(0, Qt.ItemDataRole.UserRole, comp)
                comp_item.setData(0, Qt.ItemDataRole.UserRole + 1, "competitor")
                cat_item.addChild(comp_item)

            cat_item.setExpanded(True)
            cat_item.setCheckState(0, Qt.CheckState.Checked)

    def _set_all_checked(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            for j in range(item.childCount()):
                item.child(j).setCheckState(0, state)

    def _build_run_config(self) -> Dict[str, Any]:
        """依勾選狀態產生實際要執行的監控設定（未勾選的品類/產品會被略過）。"""
        cfg = dict(self._config_data)
        selected_categories = []

        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            maobao = None
            competitors = []
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                if child.checkState(0) != Qt.CheckState.Checked:
                    continue
                prod = child.data(0, Qt.ItemDataRole.UserRole)
                kind = child.data(0, Qt.ItemDataRole.UserRole + 1)
                if kind == "maobao":
                    maobao = prod
                else:
                    competitors.append(prod)

            if maobao is None and not competitors:
                continue

            new_cat = dict(cat_item.data(0, Qt.ItemDataRole.UserRole))
            new_cat["maobao_product"] = maobao
            new_cat["competitors"] = competitors
            selected_categories.append(new_cat)

        cfg["monitor_products"] = selected_categories
        return cfg

    # ----------------------------------------------------------- 設定檔
    def _browse_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇設定檔", BASE_DIR, "JSON 設定檔 (*.json)")
        if path:
            self.cfg_edit.setText(path)
            self._load_config()

    def _load_config(self) -> None:
        path = self.cfg_edit.text()
        try:
            data = io_helper.load_config(path)
        except Exception as e:
            QMessageBox.warning(self, "設定載入失敗", str(e))
            self._append_log(f"❌ 設定載入失敗：{e}")
            return
        self._config_data = data
        self._platform_names = [p["name"] for p in data.get("platforms", [])]
        categories = data.get("monitor_products", [])
        self._rebuild_category_tree(categories)
        self._append_log(
            f"📦 已載入設定：{os.path.basename(path)}，共 {len(categories)} 個品類，"
            f"跨賣場：{', '.join(self._platform_names)}"
        )
        self.statusBar().showMessage(f"設定就緒：{len(categories)} 品類 / {len(self._platform_names)} 賣場")

    # ------------------------------------------------------------ 執行
    def _start_monitoring(self) -> None:
        if not self._config_data:
            self._append_log("❌ 尚未載入設定")
            return
        if self._worker and self._worker.isRunning():
            return
        run_config = self._build_run_config()
        if not run_config["monitor_products"]:
            QMessageBox.information(self, "尚未勾選品類", "請至少勾選一個品類（或產品）後再開始監控。")
            return

        self._set_busy(True)
        self._append_log(
            f"🚀 開始監控 {len(run_config['monitor_products'])} 個品類（勾選的子集）..."
        )
        self._worker = CrawlerWorker(run_config, parent=self)
        self._worker.log_ready.connect(self._append_log)
        self._worker.monitoring_finished.connect(self._on_monitoring_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _start_keyword_scan(self) -> None:
        keyword = self.keyword_edit.text().strip()
        if not keyword:
            self._append_log("❌ 請輸入查價關鍵字")
            return
        if not self._config_data:
            self._append_log("❌ 尚未載入設定")
            return
        if self._worker and self._worker.isRunning():
            return
        self._set_busy(True)
        self._append_log(f"🔎 開始查價關鍵字：{keyword}")
        self._worker = CrawlerWorker(self._config_data, keyword=keyword, parent=self)
        self._worker.log_ready.connect(self._append_log)
        self._worker.keyword_finished.connect(self._on_keyword_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_monitoring_finished(self, scans: List[CategoryScan], elapsed: float) -> None:
        self._set_busy(False)
        self._last_scans = scans
        self._last_elapsed = elapsed
        self._populate_scans(scans)
        n = self.table.rowCount()
        self._append_log(f"✓ 監控完成！耗時 {elapsed:.2f} 秒，共 {n} 筆結果")
        self.statusBar().showMessage(f"監控完成，耗時 {elapsed:.2f} 秒，共 {n} 筆")
        if scans:
            self._auto_export()

    def _on_keyword_finished(self, stores: List[StoreInfo], elapsed: float) -> None:
        self._set_busy(False)
        self._populate_keyword(self.keyword_edit.text().strip(), stores)
        n = self.table.rowCount()
        self._append_log(f"✓ 查價完成！耗時 {elapsed:.2f} 秒，共 {n} 筆結果")
        self.statusBar().showMessage(f"查價完成，耗時 {elapsed:.2f} 秒，共 {n} 筆")

    def _on_failed(self, msg: str) -> None:
        self._set_busy(False)
        self._append_log(f"❌ 執行失敗：{msg}")
        QMessageBox.critical(self, "執行失敗", msg)

    def _request_stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._append_log("⏹ 停止中，等待進行中的請求完成...")
            self._worker.request_stop()
            self.stop_btn.setEnabled(False)

    # ------------------------------------------------------------ 匯出
    def _auto_export(self) -> None:
        try:
            report = io_helper.build_report_data(self._last_scans, self._last_elapsed, self._platform_names)
            io_helper.save_json_report(REPORT_JSON, report)
            md = io_helper.format_markdown_report(self._last_scans, self._platform_names, self._last_elapsed)
            with open(REPORT_MD, "w", encoding="utf-8") as f:
                f.write(md)
            self._append_log(f"✓ 已自動匯出：{os.path.basename(REPORT_JSON)}、{os.path.basename(REPORT_MD)}")
        except Exception as e:
            self._append_log(f"⚠️ 自動匯出失敗：{e}")

    def _export_json(self) -> None:
        if not self._last_scans:
            self._append_log("❌ 尚無可匯出的監控結果")
            return
        path, _ = QFileDialog.getSaveFileName(self, "匯出 JSON", REPORT_JSON, "JSON 檔案 (*.json)")
        if not path:
            return
        try:
            report = io_helper.build_report_data(self._last_scans, self._last_elapsed, self._platform_names)
            io_helper.save_json_report(path, report)
            self._append_log(f"✓ 已匯出 JSON：{path}")
        except Exception as e:
            QMessageBox.warning(self, "匯出失敗", str(e))

    def _export_md(self) -> None:
        if not self._last_scans:
            self._append_log("❌ 尚無可匯出的監控結果")
            return
        path, _ = QFileDialog.getSaveFileName(self, "匯出 Markdown", REPORT_MD, "Markdown 檔案 (*.md)")
        if not path:
            return
        try:
            md = io_helper.format_markdown_report(self._last_scans, self._platform_names, self._last_elapsed)
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
            self._append_log(f"✓ 已匯出 Markdown：{path}")
        except Exception as e:
            QMessageBox.warning(self, "匯出失敗", str(e))

    # ------------------------------------------------------------ 關閉
    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.request_stop()
            self._worker.wait(8000)
        event.accept()


def main() -> None:
    app = QApplication([])
    app.setStyleSheet(THEME_QSS)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
