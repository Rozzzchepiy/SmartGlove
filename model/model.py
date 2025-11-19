import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# 1. Зчитування CSV-файлів
data_dir = "gesture_data"
samples = []
labels = []

for file in os.listdir(data_dir):
    if file.endswith(".csv"):
        label = file.split("_")[0]
        df = pd.read_csv(os.path.join(data_dir, file))
        if df.shape == (75, 39):
            samples.append(df.values.astype(float))
            labels.append(label)
        else:
            print(f"Пропускаю {file} (очікувалось 75x39, отримано {df.shape})")

samples = np.array(samples)
labels = np.array(labels)
print(f"Завантажено {len(samples)} файлів: форма {samples.shape}")

# 2. Кодування міток
encoder = LabelEncoder()
y = encoder.fit_transform(labels)

# 3. Поділ на train/test
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

# 5. Побудова моделі
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

# 7. Оцінка точності
test_loss, test_accuracy = model.evaluate(X_test_scaled, y_test, verbose=0)
print(f"Точність моделі на тестових даних: {test_accuracy * 100:.2f}%")

# 8. Збереження
model.save("gesture_lstm_model.h5")
np.save("gesture_labels.npy", encoder.classes_)
joblib.dump(scaler, "gesture_scaler.pkl")

print("Модель, scaler і мітки збережено.")
