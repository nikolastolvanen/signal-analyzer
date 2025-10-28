import os
import pandas as pd
import numpy as np


def csv_to_bin(file_path: str, save_path: str = None):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    df = pd.read_csv(file_path, low_memory=True)

    if "adc1" not in df.columns or "adc2" not in df.columns:
        raise ValueError("CSV file must contain 'adc1' and 'adc2' columns.")

    signal_1 = np.asarray(df["adc1"], dtype=np.int16)
    signal_2 = np.asarray(df["adc2"], dtype=np.int16)
    interleaved = np.column_stack((signal_1, signal_2))

    if save_path is None:
        save_path = os.path.splitext(file_path)[0] + ".bin"

    interleaved.tofile(save_path)
    return save_path
