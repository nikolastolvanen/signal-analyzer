from PySide6.QtCore import QObject, Signal
import numpy as np
from algorithms import find_peaks, compute_baseline

class PeakWorker(QObject):
    finished = Signal(np.ndarray, np.ndarray, float, float)
    error = Signal(str)

    def __init__(self, signal_1: np.ndarray, signal_2: np.ndarray):
        super().__init__()
        self.signal_1 = signal_1
        self.signal_2 = signal_2

    def run(self):
        try:

            print("Baseline computation started.")
            baseline_1 = compute_baseline(self.signal_1)
            baseline_2 = compute_baseline(self.signal_2)
            print("Baseline computation finished.")

            print("Peak detection started.")
            peaks_1 = find_peaks(self.signal_1, baseline_1)
            peaks_2 = find_peaks(self.signal_2, baseline_2)
            print("Peak detection finished.")

            self.finished.emit(peaks_1, peaks_2, baseline_1, baseline_2)

        except Exception as e:
            self.error.emit(str(e))