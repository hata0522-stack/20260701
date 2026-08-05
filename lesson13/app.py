import contextlib
import io
import os
import sys
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright
from PySide6.QtCore import QDate, QThread, QTime, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

import crawler


STATIONS = {
    "南港": "NanGang", "台北": "TaiPei", "板橋": "BanQiao",
    "桃園": "TaoYuan", "新竹": "XinZhu", "苗栗": "MiaoLi",
    "台中": "TaiZhong", "彰化": "ZhangHua", "雲林": "YunLin",
    "嘉義": "JiaYi", "台南": "TaiNan", "左營": "ZuoYing",
}

COOKIES_FILE = "thsrc_cookies.json"


class SearchWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, departure: str, arrival: str, date_text: str, time_text: str):
        super().__init__()
        self.departure = departure
        self.arrival = arrival
        self.date_text = date_text
        self.time_text = time_text

    def run(self):
        output = io.StringIO()
        try:
            cookies_path = os.path.join(os.path.dirname(__file__), COOKIES_FILE)
            with contextlib.redirect_stdout(output):
                with sync_playwright() as p:
                    crawler.crawl(
                        p=p,
                        cookies_file=cookies_path,
                        headless=False,
                        departure_station=self.departure,
                        arrival_station=self.arrival,
                        departure_date=self.date_text,
                        departure_time=self.time_text,
                    )
            self.finished.emit(output.getvalue())
        except Exception as exc:
            message = output.getvalue()
            if message:
                message += "\n"
            message += f"查詢失敗：{exc}"
            self.failed.emit(message)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: SearchWorker | None = None

        self.setWindowTitle("台灣高鐵時刻表查詢")
        self.setMinimumSize(1280, 760)
        self.resize(1280, 800)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        page_layout = QVBoxLayout(root)
        page_layout.setContentsMargins(48, 40, 48, 40)
        page_layout.setSpacing(28)

        title = QLabel("台灣高鐵時刻表查詢")
        title.setObjectName("TitleLabel")

        subtitle = QLabel("選擇出發站、到達站、日期與時間，啟動 Playwright 自動查詢高鐵時刻。")
        subtitle.setObjectName("SubtitleLabel")

        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        page_layout.addLayout(header_layout)

        card = QFrame()
        card.setObjectName("SearchCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(34, 30, 34, 30)
        card_layout.setSpacing(24)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(24)
        form_layout.setVerticalSpacing(16)

        self.departure_combo = self._station_combo("台北")
        self.arrival_combo = self._station_combo("台中")

        default_dt = datetime.now() + timedelta(hours=1)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy/MM/dd")
        self.date_edit.setDate(QDate(default_dt.year, default_dt.month, default_dt.day))
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate().addDays(28))

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(default_dt.hour, default_dt.minute))

        form_layout.addWidget(self._field_label("出發站"), 0, 0)
        form_layout.addWidget(self._field_label("到達站"), 0, 1)
        form_layout.addWidget(self._field_label("出發日期"), 0, 2)
        form_layout.addWidget(self._field_label("出發時間"), 0, 3)
        form_layout.addWidget(self.departure_combo, 1, 0)
        form_layout.addWidget(self.arrival_combo, 1, 1)
        form_layout.addWidget(self.date_edit, 1, 2)
        form_layout.addWidget(self.time_edit, 1, 3)

        card_layout.addLayout(form_layout)

        actions = QHBoxLayout()
        actions.addStretch()

        self.status_label = QLabel("尚未查詢")
        self.status_label.setObjectName("StatusLabel")

        self.search_button = QPushButton("查詢時刻表")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self.start_search)

        actions.addWidget(self.status_label)
        actions.addWidget(self.search_button)
        card_layout.addLayout(actions)
        page_layout.addWidget(card)

        result_title = QLabel("查詢輸出")
        result_title.setObjectName("SectionTitle")
        page_layout.addWidget(result_title)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("查詢結果會顯示在這裡。")
        page_layout.addWidget(self.output_text, 1)

    def _station_combo(self, default_station: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(STATIONS.keys())
        combo.setCurrentText(default_station)
        return combo

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _apply_style(self):
        app_font = QFont("PingFang TC")
        app_font.setPointSize(12)
        self.setFont(app_font)

        self.setStyleSheet("""
            QMainWindow {
                background: #f3f6fb;
            }
            QLabel#TitleLabel {
                color: #172033;
                font-size: 34px;
                font-weight: 800;
            }
            QLabel#SubtitleLabel {
                color: #607089;
                font-size: 16px;
            }
            QFrame#SearchCard {
                background: #ffffff;
                border: 1px solid #dfe7f3;
                border-radius: 22px;
            }
            QLabel#FieldLabel {
                color: #46566d;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#SectionTitle {
                color: #172033;
                font-size: 18px;
                font-weight: 800;
            }
            QLabel#StatusLabel {
                color: #607089;
                font-size: 14px;
                padding-right: 12px;
            }
            QComboBox, QDateEdit, QTimeEdit {
                min-height: 46px;
                padding: 0 14px;
                color: #172033;
                background: #f8fafd;
                border: 1px solid #cfd9e8;
                border-radius: 12px;
                font-size: 16px;
            }
            QComboBox:hover, QDateEdit:hover, QTimeEdit:hover {
                border-color: #5b8def;
                background: #ffffff;
            }
            QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {
                border: 2px solid #2f6fed;
                background: #ffffff;
            }
            QPushButton#PrimaryButton {
                min-width: 150px;
                min-height: 46px;
                padding: 0 24px;
                color: #ffffff;
                background: #2557d6;
                border: 0;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 800;
            }
            QPushButton#PrimaryButton:hover {
                background: #1f49b8;
            }
            QPushButton#PrimaryButton:disabled {
                background: #9aabc7;
            }
            QTextEdit {
                color: #dbeafe;
                background: #101827;
                border: 1px solid #22304a;
                border-radius: 18px;
                padding: 18px;
                font-family: "SF Mono", "Menlo", "Consolas", monospace;
                font-size: 14px;
                line-height: 1.45;
            }
        """)

    def start_search(self):
        departure = self.departure_combo.currentText()
        arrival = self.arrival_combo.currentText()

        if departure == arrival:
            QMessageBox.warning(self, "資料錯誤", "出發站與到達站不能相同。")
            return

        date_text = self.date_edit.date().toString("yyyy/MM/dd")
        time_text = self.time_edit.time().toString("HH:mm")

        self.output_text.setPlainText(
            f"準備查詢：{departure} → {arrival}\n"
            f"日期：{date_text}\n"
            f"時間：{time_text}\n\n"
            "正在啟動瀏覽器..."
        )
        self.status_label.setText("查詢中")
        self.search_button.setEnabled(False)

        self.worker = SearchWorker(departure, arrival, date_text, time_text)
        self.worker.finished.connect(self.search_finished)
        self.worker.failed.connect(self.search_failed)
        self.worker.start()

    def search_finished(self, output: str):
        self.output_text.setPlainText(output)
        self.status_label.setText("查詢完成")
        self.search_button.setEnabled(True)
        self.worker = None

    def search_failed(self, message: str):
        self.output_text.setPlainText(message)
        self.status_label.setText("查詢失敗")
        self.search_button.setEnabled(True)
        self.worker = None


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
