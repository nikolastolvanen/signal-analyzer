import sys
import os
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QCheckBox
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
from qtpy.QtCore import Qt
from superqt import QRangeSlider
from scipy.signal import find_peaks as scipy_find_peaks


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

        # Left panel with plot button and some file info and checkbox to show peaks
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

        self.peaks_checkbox = QCheckBox("Show peaks")
        self.peaks_checkbox.setChecked(False)
        self.peaks_checkbox.stateChanged.connect(self.on_checkbox_toggle)
        left_panel.addWidget(self.peaks_checkbox)

        left_panel.addStretch()

        # Right panel with plot view
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 4)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_panel.addWidget(self.toolbar)
        right_panel.addWidget(self.canvas)

        self.range_slider = QRangeSlider(Qt.Horizontal)
        self.range_slider.setRange(0, 100)
        self.range_slider.setValue((0, 100))
        self.range_slider.valueChanged.connect(self.on_slider_change)
        right_panel.addWidget(self.range_slider)

        self.slider_label = QLabel("Range: 0% – 100%")
        right_panel.addWidget(self.slider_label)

        self.data = None
        self.file_path = None
        self.i = None # Signal row index
        self.signal_1 = None
        self.signal_2 = None
        self.plotting_start_index = 0
        self.plotting_end_index = None
        self.signal_1_peaks = np.array([])
        self.signal_2_peaks = np.array([])

    def load_data(self):
        start_dir = os.path.expanduser("~/Documents")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            start_dir,
            "All Files (*)"
        )

        if not file_path:
            print("No file selected.")
            return

        self.file_path = file_path
        file_name = os.path.basename(file_path)
        self.file_label.setText(f"Selected file: {file_name}")
        print("Loading file:", file_path)

        try:
            self.data = pd.read_csv(file_path, low_memory=True)

            # Get file size and data points and signal duration
            file_size = os.path.getsize(file_path)
            file_size_str = self.format_size(file_size)
            num_points = len(self.data)
            signal_time_sec = num_points / 50000
            signal_time_str = self.format_time(signal_time_sec)

            # Set file size and data points and signal duration
            self.file_size_label.setText(f"File size: {file_size_str}")
            self.data_points_label.setText(f"Data points: {num_points:,}")
            self.signal_time_label.setText(f"Signal duration: {signal_time_str}")

            print(f"File loaded!!! Size: {file_size_str}, rows {num_points}, duration: {signal_time_str}")

            self.plotting_end_index = len(self.data)

            self.i = np.arange(len(self.data))
            self.signal_1 = self.data["adc1"].values if "adc1" in self.data.columns else None
            self.signal_2 = self.data["adc2"].values if "adc2" in self.data.columns else None

            # Computing peaks after data is loaded
            self.signal_1_peaks = self.find_peaks(self.signal_1)
            self.signal_2_peaks = self.find_peaks(self.signal_2)
            print("Peaks found!")
            print("Number of peaks in signal 1:", len(self.signal_1_peaks))
            print("Number of peaks in signal 2:", len(self.signal_2_peaks))

        except Exception as e:
            print("Error loading file:", e)

    def get_plotting_range(self):
        start_index = self.plotting_start_index
        end_index = self.plotting_end_index
        x_range = self.i[start_index:end_index]
        y1_range = self.signal_1[start_index:end_index] if self.signal_1 is not None else None
        y2_range = self.signal_2[start_index:end_index] if self.signal_2 is not None else None
        return x_range, y1_range, y2_range, start_index, end_index

    def plot_current_range(self):
        self.plot_signals(*self.get_plotting_range())

    def plot_data(self):
        if self.data is None:
            print("Load a data file first before plotting")
            return

        self.plot_current_range()

    def plot_signals(self, row_indexes, signal_1, signal_2, plotting_start_index, plotting_end_index):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if signal_1 is not None:
            x_down, y_down = self.minmax_downsample(row_indexes, signal_1)
            ax.plot(x_down, y_down, label='Signal 1', linewidth=0.8)

            if self.peaks_checkbox.isChecked():
                peaks_in_range = self.signal_1_peaks[(self.signal_1_peaks >= plotting_start_index) & (self.signal_1_peaks < plotting_end_index)]
                if len(peaks_in_range) > 0:
                    ax.plot(self.i[peaks_in_range], self.signal_1[peaks_in_range], "ro", label="Signal 1 peaks")

        if signal_2 is not None:
            x_down, y_down = self.minmax_downsample(row_indexes, signal_2)
            ax.plot(x_down, y_down, label='Signal 2', linewidth=0.8, alpha=0.9)

            if self.peaks_checkbox.isChecked():
                peaks_in_range = self.signal_2_peaks[(self.signal_2_peaks >= plotting_start_index) & (self.signal_2_peaks < plotting_end_index)]
                if len(peaks_in_range) > 0:
                    ax.plot(self.i[peaks_in_range], self.signal_2[peaks_in_range], "go", label="Signal 2 peaks")

        ax.set_title("Signal data")
        ax.set_xlabel("Time")
        ax.set_ylabel("Response")
        ax.legend()

        self.canvas.draw()

    def on_slider_change(self, values):
        # This function is called when the range slider is moved
        start, end = values
        self.slider_label.setText(f"Range: {start}% – {end}%")

        if self.data is not None and self.i is not None:
            total_data_points = len(self.i)
            self.plotting_start_index = int(start / 100 * total_data_points)
            self.plotting_end_index = int(end / 100 * total_data_points)
            if self.plotting_start_index < self.plotting_end_index:
                self.plot_current_range()

    def update_plot_range(self, start_ind_x, end_ind_x):
        x_range = self.i[start_ind_x:end_ind_x]
        y1_range = self.signal_1[start_ind_x:end_ind_x] if self.signal_1 is not None else None
        y2_range = self.signal_2[start_ind_x:end_ind_x] if self.signal_2 is not None else None
        self.plot_signals(x_range, y1_range, y2_range, start_ind_x, end_ind_x)

    def on_checkbox_toggle(self, state):
        if self.data is not None:
            self.plot_current_range()

    def find_peaks(self, x):
        try:
            peaks, _ = scipy_find_peaks(
                # These parameters need to be tweaked to show peaks more accurately
                x,
                height = 700,
                distance = 10000,
                prominence = 150
            )
            return peaks
        except Exception as e:
            print("Error finding peaks:", e)
            return np.array([])

    def minmax_downsample(self, x, y, n_bins=None):
        N = len(y)

        if N <= 2000:
            return x, y

        if n_bins is None:
            n_bins = max(self.canvas.width(), 2000)

        bins = np.linspace(0, N, n_bins + 1, dtype=int)
        y_min = np.minimum.reduceat(y, bins[:-1])
        y_max = np.maximum.reduceat(y, bins[:-1])
        x_mid = x[(bins[:-1] + bins[1:]) // 2]

        # print("Bins:", len(bins))

        out_len = 2 * len(x_mid)
        x_minmax = np.empty(out_len, dtype=x.dtype)
        y_minmax = np.empty(out_len, dtype=y.dtype)

        x_minmax[0::2] = x_mid
        x_minmax[1::2] = x_mid
        y_minmax[0::2] = y_min
        y_minmax[1::2] = y_max

        return x_minmax, y_minmax

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignalAnalyzer()
    window.show()
    sys.exit(app.exec())