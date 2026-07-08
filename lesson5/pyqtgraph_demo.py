"""PySide6 + pyqtgraph 功能展示

以分頁方式展示 pyqtgraph 的核心能力:
1. 曲線圖   - 多條曲線、圖例、填色、網格
2. 即時訊號 - QTimer 驅動的捲動式即時繪圖與 FPS 顯示
3. 散點圖   - 大量資料點、不同符號、點擊互動
4. 長條圖   - BarGraphItem 與 ErrorBarItem
5. 十字游標 - 滑鼠追蹤、LinearRegionItem 區間縮放(總覽 + 細節雙圖連動)
6. 影像     - ImageView 的 3D 資料時間軸播放與色彩對應表

執行:  uv run python lesson5/pyqtgraph_demo.py
測試:  uv run python lesson5/pyqtgraph_demo.py --smoke
"""

import argparse
import sys
import time

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

# 曲線配色(取自 Tailwind 色票,深色背景下辨識度高)
COLORS = ["#38bdf8", "#f472b6", "#4ade80", "#facc15", "#a78bfa", "#fb923c"]


class PyQtGraphDemo(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PySide6 + pyqtgraph 功能展示")
        self.resize(1100, 760)

        pg.setConfigOptions(antialias=True, background="#0f172a", foreground="#cbd5e1")

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._build_line_plot(), "曲線圖")
        tabs.addTab(self._build_live_plot(), "即時訊號")
        tabs.addTab(self._build_scatter_plot(), "散點圖")
        tabs.addTab(self._build_bar_plot(), "長條圖")
        tabs.addTab(self._build_crosshair_plot(), "十字游標與區間")
        tabs.addTab(self._build_image_view(), "影像")
        self.setCentralWidget(tabs)

        self.statusBar().showMessage("滑鼠拖曳可平移、滾輪可縮放、右鍵拖曳可各軸獨立縮放,點右下角 A 可重設視野")

    # ------------------------------------------------------------------
    # 1. 曲線圖:多曲線、圖例、曲線間填色
    # ------------------------------------------------------------------
    def _build_line_plot(self) -> pg.PlotWidget:
        plot = pg.PlotWidget(title="多條曲線與填色")
        plot.setLabel("bottom", "x")
        plot.setLabel("left", "y")
        plot.addLegend(offset=(10, 10))
        plot.showGrid(x=True, y=True, alpha=0.3)

        x = np.linspace(0, 4 * np.pi, 600)
        sin_curve = plot.plot(x, np.sin(x), pen=pg.mkPen(COLORS[0], width=2), name="sin(x)")
        cos_curve = plot.plot(x, np.cos(x), pen=pg.mkPen(COLORS[1], width=2), name="cos(x)")

        # 兩條曲線之間填色
        fill = pg.FillBetweenItem(sin_curve, cos_curve, brush=pg.mkBrush(56, 189, 248, 40))
        plot.addItem(fill)

        # 阻尼震盪:虛線 + 資料點符號
        damped = np.sin(x * 2) * np.exp(-x / 6)
        plot.plot(
            x[::12],
            damped[::12],
            pen=pg.mkPen(COLORS[2], width=2, style=QtCore.Qt.PenStyle.DashLine),
            symbol="o",
            symbolSize=6,
            symbolBrush=COLORS[2],
            symbolPen=None,
            name="阻尼震盪",
        )
        return plot

    # ------------------------------------------------------------------
    # 2. 即時訊號:QTimer 更新、多通道、FPS 統計
    # ------------------------------------------------------------------
    def _build_live_plot(self) -> pg.PlotWidget:
        self.live_plot = pg.PlotWidget(title="即時捲動訊號(50ms 更新)")
        self.live_plot.setLabel("bottom", "樣本")
        self.live_plot.setLabel("left", "數值")
        self.live_plot.addLegend(offset=(10, 10))
        self.live_plot.showGrid(x=True, y=True, alpha=0.3)
        self.live_plot.setYRange(-3, 3)

        n = 300
        self.live_data = [np.zeros(n), np.zeros(n)]
        self.live_curves = [
            self.live_plot.plot(self.live_data[0], pen=pg.mkPen(COLORS[2], width=2), name="平滑雜訊"),
            self.live_plot.plot(self.live_data[1], pen=pg.mkPen(COLORS[3], width=2), name="正弦 + 雜訊"),
        ]

        self.fps_label = pg.TextItem(color="#94a3b8")
        self.live_plot.addItem(self.fps_label, ignoreBounds=True)
        self.fps_label.setPos(0, 2.8)

        self._phase = 0.0
        self._last_time = time.perf_counter()
        self._fps = 0.0

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._update_live_plot)
        self.timer.start()
        return self.live_plot

    def _update_live_plot(self) -> None:
        self._phase += 0.15

        # 通道 1:自我相關的平滑隨機訊號
        self.live_data[0] = np.roll(self.live_data[0], -1)
        self.live_data[0][-1] = self.live_data[0][-2] * 0.92 + np.random.normal(scale=0.35)

        # 通道 2:正弦波加上量測雜訊
        self.live_data[1] = np.roll(self.live_data[1], -1)
        self.live_data[1][-1] = 1.5 * np.sin(self._phase) + np.random.normal(scale=0.1)

        for curve, data in zip(self.live_curves, self.live_data):
            curve.setData(data)

        now = time.perf_counter()
        self._fps = self._fps * 0.9 + (1.0 / max(now - self._last_time, 1e-6)) * 0.1
        self._last_time = now
        self.fps_label.setText(f"更新率:{self._fps:.1f} FPS")

    # ------------------------------------------------------------------
    # 3. 散點圖:三群資料、不同符號、點擊變色
    # ------------------------------------------------------------------
    def _build_scatter_plot(self) -> pg.PlotWidget:
        plot = pg.PlotWidget(title="散點圖(點擊資料點試試)")
        plot.setLabel("bottom", "x")
        plot.setLabel("left", "y")
        plot.addLegend(offset=(10, 10))
        plot.showGrid(x=True, y=True, alpha=0.3)

        rng = np.random.default_rng(42)
        clusters = [
            ("群組 A", "o", COLORS[0], rng.normal([0, 0], 0.8, size=(150, 2))),
            ("群組 B", "s", COLORS[1], rng.normal([4, 3], 1.0, size=(150, 2))),
            ("群組 C", "t", COLORS[2], rng.normal([-2, 4], 0.6, size=(150, 2))),
        ]
        for name, symbol, color, points in clusters:
            scatter = pg.ScatterPlotItem(
                pos=points,
                symbol=symbol,
                size=9,
                brush=pg.mkBrush(color),
                pen=None,
                hoverable=True,
                hoverSize=13,
            )
            scatter.sigClicked.connect(self._on_scatter_clicked)
            plot.addItem(scatter)
            # 圖例用小樣本代表
            plot.plot([], [], pen=None, symbol=symbol, symbolBrush=color, symbolSize=9, name=name)
        return plot

    def _on_scatter_clicked(self, _scatter: pg.ScatterPlotItem, points: list) -> None:
        for point in points:
            point.setBrush(pg.mkBrush("#f8fafc"))
            point.setSize(14)
        self.statusBar().showMessage(
            f"點擊了 {len(points)} 個資料點,座標:({points[0].pos().x():.2f}, {points[0].pos().y():.2f})"
        )

    # ------------------------------------------------------------------
    # 4. 長條圖:BarGraphItem + 誤差線 + 自訂座標軸文字
    # ------------------------------------------------------------------
    def _build_bar_plot(self) -> pg.PlotWidget:
        plot = pg.PlotWidget(title="每月平均值與誤差線")
        plot.setLabel("left", "數值")
        plot.showGrid(y=True, alpha=0.3)

        rng = np.random.default_rng(7)
        months = ["一月", "二月", "三月", "四月", "五月", "六月"]
        x = np.arange(len(months))
        values = rng.uniform(30, 90, size=len(months))
        errors = rng.uniform(3, 9, size=len(months))

        bars = pg.BarGraphItem(x=x, height=values, width=0.6, brush=pg.mkBrush(COLORS[4]), pen=None)
        error_bars = pg.ErrorBarItem(
            x=x, y=values, height=errors * 2, beam=0.2, pen=pg.mkPen("#e2e8f0", width=1.5)
        )
        plot.addItem(bars)
        plot.addItem(error_bars)

        # 底部座標軸顯示月份名稱
        axis = plot.getAxis("bottom")
        axis.setTicks([list(zip(x, months))])
        plot.setXRange(-0.7, len(months) - 0.3)
        return plot

    # ------------------------------------------------------------------
    # 5. 十字游標與區間:雙圖連動(上方細節、下方總覽)
    # ------------------------------------------------------------------
    def _build_crosshair_plot(self) -> pg.GraphicsLayoutWidget:
        widget = pg.GraphicsLayoutWidget()

        x = np.linspace(0, 100, 3000)
        y = np.sin(x * 0.8) + 0.5 * np.sin(x * 3.1) + np.random.default_rng(1).normal(0, 0.15, x.size)

        # 上方:細節圖(顯示選取區間)
        self.detail_plot = widget.addPlot(row=0, col=0, title="細節(移動滑鼠顯示座標)")
        self.detail_plot.showGrid(x=True, y=True, alpha=0.3)
        self.detail_plot.plot(x, y, pen=pg.mkPen(COLORS[0], width=1))

        # 下方:總覽圖(拖曳黃色區間改變上方顯示範圍)
        overview = widget.addPlot(row=1, col=0, title="總覽(拖曳區間選取範圍)")
        overview.setMaximumHeight(160)
        overview.plot(x, y, pen=pg.mkPen("#64748b", width=1))

        self.region = pg.LinearRegionItem([20, 40], brush=pg.mkBrush(250, 204, 21, 40))
        overview.addItem(self.region)
        self.region.sigRegionChanged.connect(
            lambda: self.detail_plot.setXRange(*self.region.getRegion(), padding=0)
        )
        # 在細節圖平移/縮放時,同步更新區間位置
        self.detail_plot.sigXRangeChanged.connect(
            lambda _, rng: self.region.setRegion(rng)
        )
        self.detail_plot.setXRange(20, 40, padding=0)

        # 十字游標與座標標籤
        self.v_line = pg.InfiniteLine(angle=90, pen=pg.mkPen("#f8fafc", width=0.8))
        self.h_line = pg.InfiniteLine(angle=0, pen=pg.mkPen("#f8fafc", width=0.8))
        self.coord_label = pg.LabelItem(justify="right")
        widget.addItem(self.coord_label, row=2, col=0)
        self.detail_plot.addItem(self.v_line, ignoreBounds=True)
        self.detail_plot.addItem(self.h_line, ignoreBounds=True)

        self._mouse_proxy = pg.SignalProxy(
            self.detail_plot.scene().sigMouseMoved, rateLimit=60, slot=self._on_mouse_moved
        )
        return widget

    def _on_mouse_moved(self, event: tuple) -> None:
        pos = event[0]
        if not self.detail_plot.sceneBoundingRect().contains(pos):
            return
        point = self.detail_plot.vb.mapSceneToView(pos)
        self.v_line.setPos(point.x())
        self.h_line.setPos(point.y())
        self.coord_label.setText(f"x = {point.x():.2f}, y = {point.y():.2f}")

    # ------------------------------------------------------------------
    # 6. 影像:3D 資料(時間 x 寬 x 高),ImageView 內建時間軸與播放
    # ------------------------------------------------------------------
    def _build_image_view(self) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)

        hint = QtWidgets.QLabel("拖曳下方時間軸或按空白鍵播放動畫;右側直方圖可調整顯示範圍與色彩")
        hint.setStyleSheet("color: #94a3b8; padding: 4px;")
        layout.addWidget(hint)

        image_view = pg.ImageView()
        x = np.linspace(-3, 3, 220)
        xx, yy = np.meshgrid(x, x)

        # 產生 60 個時間影格的波動干涉圖樣
        frames = np.empty((60, *xx.shape))
        for i, t in enumerate(np.linspace(0, 2 * np.pi, 60)):
            frames[i] = np.sin(xx * 3 + t) * np.cos(yy * 4 - t) * np.exp(-(xx**2 + yy**2) / 7)

        image_view.setImage(frames, xvals=np.linspace(0, 1, 60))
        image_view.setColorMap(pg.colormap.get("viridis"))
        layout.addWidget(image_view)
        return container


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="建立視窗後直接結束,不進入 Qt 事件迴圈(供自動化測試使用)。",
    )
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = PyQtGraphDemo()

    if args.smoke:
        print("PySide6 與 pyqtgraph 載入成功,共建立 6 個展示分頁。")
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
