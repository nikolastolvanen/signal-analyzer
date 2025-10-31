import sys
import os
import pandas as pd
import numpy as np
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtCore import QThread
from workers import PeakWorker
from formatters import format_size, format_time
from algorithms import find_peaks, minmax_downsample
from converter import csv_to_bin
from main_window import MainWindow


class SignalAnalyzer(MainWindow):
    def __init__(self):
        super().__init__()

        self.i = None
        self.file_path = None
        self.signal_1 = None
        self.signal_2 = None
        self.time = None
        self.sampling_rate = 50000
        self.plotting_start_index = 0
        self.plotting_end_index = None
        self.signal_1_peaks = np.array([])
        self.signal_2_peaks = np.array([])

        self.open_action.triggered.connect(self.load_data)
        self.convert_action.triggered.connect(self.convert_file_to_bin)
        self.exit_action.triggered.connect(self.close)
        self.plot_button.clicked.connect(self.plot_data)
        self.peaks_checkbox.stateChanged.connect(self.on_checkbox_toggle)
        self.range_slider.valueChanged.connect(self.on_slider_change)
        self.range_button.clicked.connect(self.reset_slider_range)

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

        file_type = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        file_size_str = format_size(file_size)

        try:

            if file_type == ".csv":

                self.i = pd.read_csv(file_path, low_memory=True)
                number_of_points = len(self.i)
                self.signal_1 = self.i["adc1"].values
                self.signal_2 = self.i["adc2"].values

            elif file_type == ".bin":

                number_of_samples = file_size // (2 * np.dtype(np.int16).itemsize)
                raw_data = np.memmap(file_path, dtype=np.int16, mode="r", shape=(number_of_samples, 2))
                self.signal_1 = raw_data[:, 0]
                self.signal_2 = raw_data[:, 1]
                number_of_points = len(raw_data)
                self.i = pd.DataFrame({"adc1": self.signal_1, "adc2": self.signal_2})

            else:
                print("This file type is not supported.")
                return

            print("File loaded!!!")

            signal_time_sec = number_of_points / self.sampling_rate
            signal_time_str = format_time(signal_time_sec)

            self.file_size_label.setText(f"File size: {file_size_str}")
            self.data_points_label.setText(f"Data points: {number_of_points:,}")
            self.signal_time_label.setText(f"Signal duration: {signal_time_str}")

            self.plotting_end_index = len(self.i)
            self.i = np.arange(len(self.i))
            self.time = self.i / self.sampling_rate

            # Peak detection
            self.thread = QThread()
            self.worker = PeakWorker(self.signal_1, self.signal_2)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_peaks_detection_finished)
            self.worker.error.connect(self.on_peaks_detection_error)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as e:
            print("Error loading file:", e)

    def on_peaks_detection_finished(self, peaks_1, peaks_2):
        self.signal_1_peaks = peaks_1
        self.signal_2_peaks = peaks_2
        print("Number of peaks in signal 1:", len(peaks_1))
        print("Number of peaks in signal 2:", len(peaks_2))

    def on_peaks_detection_error(self, message):
        print("Error detecting peaks:", message)

    def convert_file_to_bin(self):
        start_dir = os.path.expanduser("~/Documents")
        file_path, _ = QFileDialog.getOpenFileName(self,"Select a file", start_dir,"All files (*)")

        if not file_path:
            print("No file selected.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save as .bin",
            os.path.splitext(file_path)[0] + ".bin",
            "Binary files (*.bin)"
        )
        if not save_path:
            print("Save cancelled.")
            return

        saved_file = csv_to_bin(file_path, save_path)
        print(f"File converted and saved to: {saved_file}")

    def get_plotting_range(self):
        start = self.plotting_start_index
        end = self.plotting_end_index
        x_range = self.i[start:end]
        y1_range = self.signal_1[start:end]
        y2_range = self.signal_2[start:end]
        return x_range, y1_range, y2_range, start, end

    def plot_current_range(self):
        self.plot_signals(*self.get_plotting_range())

    def plot_data(self):
        if self.i is None:
            print("Load a data file first before plotting")
            return

        self.plot_current_range()

    def plot_signals(self, row_indexes, signal_1, signal_2, plotting_start_index, plotting_end_index):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if signal_1 is not None:
            time_range = self.time[plotting_start_index:plotting_end_index]
            x_down, y_down = minmax_downsample(time_range, signal_1, canvas_width=self.canvas.width())
            ax.plot(x_down, y_down, label='Signal 1', linewidth=0.8)

            if self.peaks_checkbox.isChecked():
                peaks_in_range = self.signal_1_peaks[(self.signal_1_peaks >= plotting_start_index) & (self.signal_1_peaks < plotting_end_index)]
                if len(peaks_in_range) > 0:
                    ax.plot(self.time[peaks_in_range], self.signal_1[peaks_in_range], "ro", label="Signal 1 peaks")

        if signal_2 is not None:
            time_range = self.time[plotting_start_index:plotting_end_index]
            x_down, y_down = minmax_downsample(time_range, signal_2, canvas_width=self.canvas.width())
            ax.plot(x_down, y_down, label='Signal 2', linewidth=0.8, alpha=0.9)

            if self.peaks_checkbox.isChecked():
                peaks_in_range = self.signal_2_peaks[(self.signal_2_peaks >= plotting_start_index) & (self.signal_2_peaks < plotting_end_index)]
                if len(peaks_in_range) > 0:
                    ax.plot(self.time[peaks_in_range], self.signal_2[peaks_in_range], "go", label="Signal 2 peaks")

        ax.set_title("Signal data")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Response")
        ax.legend()

        self.canvas.draw()

    def on_slider_change(self, values):
        start, end = values
        self.slider_label.setText(f"Range: {start}% – {end}%")

        if self.i is not None and self.i is not None:
            total_data_points = len(self.i)
            self.plotting_start_index = int(start / 100 * total_data_points)
            self.plotting_end_index = int(end / 100 * total_data_points)
            if self.plotting_start_index < self.plotting_end_index:
                self.plot_current_range()

    def reset_slider_range(self):
        if self.i is None:
            return

        self.range_slider.setValue((0, 100))
        self.slider_label.setText("Range: 0% – 100%")
        self.plotting_start_index = 0
        self.plotting_end_index = len(self.i)
        self.plot_current_range()

    def on_checkbox_toggle(self, _):
        if self.i is not None:
            self.plot_current_range()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignalAnalyzer()
    window.show()
    sys.exit(app.exec())