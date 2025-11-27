import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# Додаємо шлях до батьківської директорії, де знаходиться папка Server
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Імпортуємо з Server/server.py
from Server.server import (
    resample_sequence,
    SEQUENCE_LENGTH,
    EXPECTED_COLUMNS
)

# Абсолютний шлях до gesture_data у Server/
gesture_data_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Server", "gesture_data")
)

# 1. Зчитування CSV-файлів
data_dir = gesture_data_path
samples = []
labels = []

for file in os.listdir(data_dir):
    if file.endswith(".csv"):
        label = file.split("_")[0]
        df = pd.read_csv(os.path.join(data_dir, file))

        # Перевірка кількості колонок
        if df.shape[1] != EXPECTED_COLUMNS:
            print(f"Пропускаю {file} — очікується {EXPECTED_COLUMNS} колонок, отримано {df.shape[1]}")
            continue

        # Ресемплінг
        df_resampled = resample_sequence(df, SEQUENCE_LENGTH)

        # Остаточна перевірка після ресемплінгу
        if df_resampled.shape != (SEQUENCE_LENGTH, EXPECTED_COLUMNS):
            print(f"Пропускаю {file} після ресемплінгу — отримано {df_resampled.shape}")
            continue

        samples.append(df_resampled.values.astype(float))
        labels.append(label)

samples = np.array(samples)
labels = np.array(labels)
print(f"Завантажено {len(samples)} файлів: форма {samples.shape}")

# 2. Кодування міток
encoder = LabelEncoder()
y = encoder.fit_transform(labels)

# 3. train/test split
X_train, X_test, y_train, y_test = train_test_split(
    samples, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Масштабування
scaler = MinMaxScaler()
N_train, T, F = X_train.shape
N_test = X_test.shape[0]

X_train_2d = X_train.reshape(-1, F)
X_test_2d = X_test.reshape(-1, F)

scaler.fit(X_train_2d)
X_train_scaled = scaler.transform(X_train_2d).reshape(N_train, T, F)
X_test_scaled = scaler.transform(X_test_2d).reshape(N_test, T, F)

# 5. Модель
model = Sequential([
    LSTM(128, input_shape=(T, F)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dense(len(np.unique(y)), activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# 6. Навчання
history = model.fit(
    X_train_scaled, y_train,
    validation_data=(X_test_scaled, y_test),
    epochs=50,
    batch_size=8,
    verbose=1
)

# 7. Оцінка
test_loss, test_accuracy = model.evaluate(X_test_scaled, y_test, verbose=0)
print(f"Точність моделі на тестових даних: {test_accuracy * 100:.2f}%")

# 8. Збереження
model.save("gesture_lstm_model.h5")
np.save("gesture_labels.npy", encoder.classes_)
joblib.dump(scaler, "gesture_scaler.pkl")

print("Модель, scaler і мітки збережено.")
