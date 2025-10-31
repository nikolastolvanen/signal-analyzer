from PySide6.QtCore import QObject, Signal
import numpy as np
from algorithms import find_peaks

class PeakWorker(QObject):
    finished = Signal(np.ndarray, np.ndarray)
    error = Signal(str)

    def __init__(self, signal_1: np.ndarray, signal_2: np.ndarray):
        super().__init__()
        self.signal_1 = signal_1
        self.signal_2 = signal_2

    def run(self):
        try:
            print("Peak detection started.")
            peaks_1 = find_peaks(self.signal_1)
            peaks_2 = find_peaks(self.signal_2)
            print("Peak detection ended.")
            self.finished.emit(peaks_1, peaks_2)
        except Exception as e:
            self.error.emit(str(e))
