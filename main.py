import sys
import os
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
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
        self.resize(1000, 600)

        # Toolbar on top
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        open_action = file_menu.addAction("Open")
        open_action.triggered.connect(self.load_data)
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Main layout
        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Left panel with plot button and some file info
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1)

        self.file_label = QLabel("Selected file: None")
        left_panel.addWidget(self.file_label)

        self.file_size_label = QLabel("File size: --")
        left_panel.addWidget(self.file_size_label)

        self.data_points_label = QLabel("Data points: --")
        left_panel.addWidget(self.data_points_label)

        self.signal_time_label = QLabel("Signal duration: --")
        left_panel.addWidget(self.signal_time_label)

        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot_data)
        left_panel.addWidget(self.plot_button)
        left_panel.addStretch()

        # Right panel with plot view
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 4)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_panel.addWidget(self.toolbar)
        right_panel.addWidget(self.canvas)

        self.data = None
        self.file_path = None

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

        self.file_path = file_path
        file_name = os.path.basename(file_path)
        self.file_label.setText(f"Selected file: {file_name}")
        print("Loaded file:", file_path)

        try:
            # Try to load CSV file
            self.data = pd.read_csv(file_path, low_memory=True)

            # This removes empty rows
            self.data.dropna(how='all', inplace=True)

            # File size and data points and signal duration
            file_size = os.path.getsize(file_path)
            file_size_str = self.format_size(file_size)
            num_points = len(self.data)
            signal_time_sec = num_points / 50000
            signal_time_str = self.format_time(signal_time_sec)

            self.file_size_label.setText(f"File size: {file_size_str}")
            self.data_points_label.setText(f"Data points: {num_points:,}")
            self.signal_time_label.setText(f"Signal duration: {signal_time_str}")

            print(f"File loaded!!! Size: {file_size_str}, rows {num_points}, duration: {signal_time_str}")

        except Exception as e:
            print("Error loading file:", e)
            self.file_size_label.setText("File size: --")
            self.data_points_label.setText("Data points: --")
            self.signal_time_label.setText("Signal duration: --")

    def format_size(self, size_bytes):
        # This function formats the file size to look good
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / (1024**2):.1f} MB"
        else:
            return f"{size_bytes / (1024**3):.1f} GB"

    def format_time(self, seconds):
        # This function formats the signal duration time to easy to understand format
        if seconds < 1:
            return f"{seconds * 1000:.1f} ms"
        elif seconds < 60:
            return f"{seconds:.2f} s"
        elif seconds < 3600:
            m, s = divmod(seconds, 60)
            return f"{int(m)} min {s:.1f} s"
        else:
            h, rem = divmod(seconds, 3600)
            m, s = divmod(rem, 60)
            return f"{int(h)} h {int(m)} min"

    def minmax_downsample(self, x, y, n_bins=10_000):
        N = len(y)

        if N <= n_bins * 2:
            return x, y

        indices = (np.arange(N) * n_bins) // N
        starts = np.flatnonzero(np.r_[True, np.diff(indices) > 0])
        starts = np.r_[starts, N]

        y_min = np.minimum.reduceat(y, starts[:-1])
        y_max = np.maximum.reduceat(y, starts[:-1])

        x_mid = x[(starts[:-1] + starts[1:]) // 2]

        out_len = 2 * len(x_mid)
        x_minmax = np.empty(out_len, dtype=x.dtype)
        y_minmax = np.empty(out_len, dtype=y.dtype)

        x_minmax[0::2] = x_mid
        x_minmax[1::2] = x_mid
        y_minmax[0::2] = y_min
        y_minmax[1::2] = y_max

        return x_minmax, y_minmax

    def plot_data(self):
        if self.data is None:
            print("Load a data file first before plotting")
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
