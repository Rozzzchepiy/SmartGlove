import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout

# Додаємо шлях до батьківської директорії
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Імпорт функцій з Server
from Server.server import (
    resample_sequence,
    SEQUENCE_LENGTH,
    EXPECTED_COLUMNS
)

# Шлях до gesture_data
gesture_data_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "gesture_data")
)

# -------------------------------
# 1. Зчитування CSV-файлів
# -------------------------------
samples = []
labels = []

for file in os.listdir(gesture_data_path):
    if file.endswith(".csv"):
        label = file.split("_")[0]
        df = pd.read_csv(os.path.join(gesture_data_path, file))

        # Перевірка кількості колонок
        if df.shape[1] != EXPECTED_COLUMNS:
            print(f"Пропускаю {file} — очікується {EXPECTED_COLUMNS} колонок, отримано {df.shape[1]}")
            continue

        # Ресемплінг
        df_resampled = resample_sequence(df, SEQUENCE_LENGTH)

        if df_resampled.shape != (SEQUENCE_LENGTH, EXPECTED_COLUMNS):
            print(f"Пропускаю {file} після ресемплінгу — отримано {df_resampled.shape}")
            continue

        samples.append(df_resampled.values.astype(float))
        labels.append(label)

samples = np.array(samples)
labels = np.array(labels)
print(f"Завантажено {len(samples)} файлів: форма {samples.shape}")

# -------------------------------
# 2. Кодування міток
# -------------------------------
encoder = LabelEncoder()
y = encoder.fit_transform(labels)

# -------------------------------
# 3. Stratified train/test split
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    samples, y,
    test_size=0.2,
    random_state=42,
    stratify=y  # забезпечує правильне розділення по класах
)

# -------------------------------
# 4. Масштабування
# -------------------------------
scaler = MinMaxScaler()
N_train, T, F = X_train.shape
N_test = X_test.shape[0]

X_train_2d = X_train.reshape(-1, F)
X_test_2d = X_test.reshape(-1, F)

scaler.fit(X_train_2d)
X_train_scaled = scaler.transform(X_train_2d).reshape(N_train, T, F)
X_test_scaled = scaler.transform(X_test_2d).reshape(N_test, T, F)

# -------------------------------
# 5. Модель LSTM(32) з Input шаром
# -------------------------------
model = Sequential([
    Input(shape=(T, F)),       # Забирає попередження input_shape
    LSTM(32, return_sequences=False),  # 32 юніти
    Dropout(0.3),               # трохи більше регуляризації
    Dense(64, activation='relu'),  # Dense шар перед виходом
    Dropout(0.2),
    Dense(len(np.unique(y)), activation='softmax')  # вихідний шар
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# -------------------------------
# 6. Навчання
# -------------------------------
history = model.fit(
    X_train_scaled, y_train,
    validation_data=(X_test_scaled, y_test),
    epochs=50,
    batch_size=4,
    verbose=1
)

# -------------------------------
# 7. Оцінка
# -------------------------------
test_loss, test_accuracy = model.evaluate(X_test_scaled, y_test, verbose=0)
print(f"Точність моделі на тестових даних: {test_accuracy * 100:.2f}%")

# -------------------------------
# 8. Збереження
# -------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))

model.save(os.path.join(script_dir, "gesture_lstm32_model.keras"))
np.save(os.path.join(script_dir, "gesture_labels.npy"), encoder.classes_)
joblib.dump(scaler, os.path.join(script_dir, "gesture_scaler.pkl"))

print("Модель, scaler і мітки збережено.")
