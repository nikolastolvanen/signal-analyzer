import sys
import os
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QVBoxLayout, QWidget, QPushButton
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure


class SignalAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal analyzer")
        self.resize(800, 600)

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.load_button = QPushButton("Load data")
        self.load_button.clicked.connect(self.load_data)
        layout.addWidget(self.load_button)

        self.data = None

    def load_data(self):
        start_dir = os.path.expanduser("~/Documents")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            start_dir,
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            print("No file selected.")
            return

        print("Loaded file:", file_path)

        try:
            self.data = pd.read_csv(file_path, low_memory=True)
            self.plot_data()
        except Exception as e:
            print("Error loading file:", e)

    def minmax_downsample(self, x, y, n_bins=10000):
        if len(y) <= n_bins * 2:
            return x, y

        indices = np.linspace(0, len(y), n_bins + 1, dtype=int)
        x_minmax = np.empty(n_bins * 2)
        y_minmax = np.empty(n_bins * 2)

        for i in range(n_bins):
            start, end = indices[i], indices[i + 1]
            if start == end:
                continue
            segment = y[start:end]
            y_min, y_max = np.min(segment), np.max(segment)
            x_mid = x[start + len(segment) // 2]
            x_minmax[2 * i] = x_mid
            y_minmax[2 * i] = y_min
            x_minmax[2 * i + 1] = x_mid
            y_minmax[2 * i + 1] = y_max

        return x_minmax, y_minmax

    def plot_data(self):
        if self.data is None:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        x = np.arange(len(self.data))
        n_points = len(x)
        n_bins = 10000 if n_points > 20000 else n_points // 2

        if 'adc1' in self.data.columns:
            x_down, y_down = self.minmax_downsample(x, self.data['adc1'].values, n_bins=n_bins)
            ax.plot(x_down, y_down, label='Signal 1', linewidth=0.8)

        if 'adc2' in self.data.columns:
            x_down, y_down = self.minmax_downsample(x, self.data['adc2'].values, n_bins=n_bins)
            ax.plot(x_down, y_down, label='Signal 2', linewidth=0.8, alpha=0.9)

        ax.set_title("Signal data")
        ax.set_xlabel("Time")
        ax.set_ylabel("Response")
        ax.legend()

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignalAnalyzer()
    window.show()
    sys.exit(app.exec())
