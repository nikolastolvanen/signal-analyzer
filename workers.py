from PySide6.QtCore import QObject, Signal
import numpy as np
from algorithms import find_peaks, compute_baseline

class PeakWorker(QObject):
    finished = Signal(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float)
    error = Signal(str)

    def __init__(self, signal_1: np.ndarray, signal_2: np.ndarray):
        super().__init__()
        self.signal_1 = signal_1
        self.signal_2 = signal_2
        self.section_size = 600000

    def process_signal(self, signal: np.ndarray):
        signal_length = len(signal)

        baselines = []
        all_tumor_peaks = []
        all_water_peaks = []
        total_tumor_size = 0
        total_signal_sd = np.std(signal)

        for sect in range(0, signal_length, self.section_size):
            start = sect
            end = min(start + self.section_size, signal_length)
            section = signal[start:end]

            section_sd = np.std(section)
            section_mean = np.mean(section)

            section_bl = compute_baseline(section)
            baselines.append(np.full_like(section, section_bl, dtype=float))

            tumor_peaks, water_peaks, tumor_size = find_peaks(section, section_bl, section_sd, section_mean, total_signal_sd)

            all_tumor_peaks.extend(tumor_peaks + start)
            all_water_peaks.extend(water_peaks + start)
            total_tumor_size += tumor_size

        full_baseline = np.concatenate(baselines)
        return np.array(all_tumor_peaks), np.array(all_water_peaks), full_baseline, total_tumor_size


    def run(self):
        try:

            print("Baseline computation and peak detection started.")
            tumor_peaks_1, water_peaks_1, baseline_1, total_tumor_size_1 = self.process_signal(self.signal_1)
            tumor_peaks_2, water_peaks_2, baseline_2, total_tumor_size_2 = self.process_signal(self.signal_2)
            print("Baseline computation and peak detection ended.")

            self.finished.emit(tumor_peaks_1, tumor_peaks_2, water_peaks_1, water_peaks_2, baseline_1, baseline_2, total_tumor_size_1, total_tumor_size_2)

        except Exception as e:
            self.error.emit(str(e))