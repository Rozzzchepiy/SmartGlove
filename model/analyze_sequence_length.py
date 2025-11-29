import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Шлях до gesture_data
gesture_data_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Server", "gesture_data")
)

lengths = []

# Зчитування довжин всіх CSV-файлів
for file in os.listdir(gesture_data_path):
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(gesture_data_path, file))
        lengths.append(len(df))

lengths = np.array(lengths)

print(f"Знайдено {len(lengths)} CSV-файлів")
print(f"Мінімальна довжина: {lengths.min()}")
print(f"Максимальна довжина: {lengths.max()}")
print(f"Середня довжина: {lengths.mean():.2f}")
print(f"Медіана довжини: {np.median(lengths)}")

# Пропозиція SEQUENCE_LENGTH: можна взяти медіану або округлити
recommended_length = int(np.median(lengths))
print(f"Рекомендована SEQUENCE_LENGTH: {recommended_length}")
