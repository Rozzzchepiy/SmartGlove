import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model

# 1. Завантажуємо модель, scaler і мітки
model = load_model("gesture_lstm_model.h5")
scaler = joblib.load("gesture_scaler.pkl")
classes = np.load("gesture_labels.npy", allow_pickle=True)

# 2. Функція передбачення
def predict_gesture(csv_path):
    # зчитуємо CSV
    df = pd.read_csv(csv_path)
    data = df.values.astype(float)

    # перевіряємо розмірність
    if data.shape != (75, 39):
        raise ValueError(f"Очікувалось (75, 39), отримано {data.shape}")

    # масштабуємо за збереженим scaler
    data_scaled = scaler.transform(data)

    # додаємо batch-вісь (1, 75, 39)
    data_scaled = np.expand_dims(data_scaled, axis=0)

    # передбачаємо
    pred = model.predict(data_scaled, verbose=0)
    label = classes[np.argmax(pred)]
    confidence = np.max(pred)

    return label, confidence


# 3. Використання (приклад)
if __name__ == "__main__":
    csv_file = "gesture_data/test_gesture.csv"  # шлях до нового CSV
    label, conf = predict_gesture(csv_file)
    print(f"Жест: {label} (впевненість {conf*100:.2f}%)")
