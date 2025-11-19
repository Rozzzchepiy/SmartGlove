import os
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model

# --- НАЛАШТУВАННЯ ВІДПОВІДНО ДО НОВОЇ МОДЕЛІ ---

# Цільова довжина послідовності після обробки (залишається 75)
SEQUENCE_LENGTH = 75

# Очікувана кількість колонок (ознак) від сенсорів (оновлено з 27 до 39)
EXPECTED_COLUMNS = 39

# Нові імена файлів
MODEL_NAME = "gesture_lstm_model.h5"
SCALER_NAME = "gesture_scaler.pkl"
LABELS_NAME = "gesture_labels.npy"

app = Flask(__name__)

# Глобальні змінні для моделі, скейлера та міток
model = None
scaler = None
classes = None


def resample_sequence(df: pd.DataFrame, target_length: int) -> pd.DataFrame:
    """
    Приводить кількість рядків у df до target_length.
    Якщо рядків менше — виконує інтерполяцію.
    Якщо більше — рівномірно вибирає точки.
    
    Args:
        df: pandas DataFrame із часовими даними (один жест)
        target_length: бажана кількість точок після вирівнювання
        
    Returns:
        pandas DataFrame тієї ж структури, але з target_length рядків
    """
    # Завжди скидаємо індекс для чистої роботи
    df = df.reset_index(drop=True)
    current_length = len(df)

    # якщо даних менше → інтерполюємо (новий, надійний метод)
    if current_length < target_length:
        # 1. Створюємо новий дробовий індекс, що відповідає цільовій довжині
        new_index = np.linspace(0, current_length - 1, target_length)
        
        # 2. Розширюємо DataFrame до нового індексу. 
        #    Точки, що не існували, заповняться значеннями NaN.
        df_resampled = df.reindex(new_index)
        
        # 3. Інтерполюємо (заповнюємо) пропущені значення NaN лінійно
        df_resampled = df_resampled.interpolate(method='linear')
        
        return df_resampled.reset_index(drop=True)

    # якщо даних більше → рівномірно вибираємо точки (цей метод працював правильно)
    elif current_length > target_length:
        indices = np.linspace(0, current_length - 1, target_length, dtype=int)
        df_resampled = df.iloc[indices].reset_index(drop=True)
        return df_resampled

    # якщо вже рівно — нічого не робимо
    else:
        return df


def load_ai_components():
    """Завантажує всі компоненти AI: модель, скейлер та мітки класів."""
    global model, scaler, classes
    
    try:
        # Перевіряємо наявність всіх необхідних файлів
        if all(os.path.exists(f) for f in [MODEL_NAME, SCALER_NAME, LABELS_NAME]):
            scaler = joblib.load(SCALER_NAME)
            print("Скалер завантажено")
            
            classes = np.load(LABELS_NAME, allow_pickle=True)
            print("мітки класів завантажено")
            
            # Keras/TensorFlow модель завантажується спеціальною функцією
            model = load_model(MODEL_NAME)
            print("Модель Keras завантажена, сервер в режимі розпізнавання")
            return True
        else:
            print("Один або більше файлів моделі не знайдено, сервер в режимі ЗБОРУ ДАНИХ")
            return False
    except Exception as e:
        print(f"Помилка завантаження AI компонентів: {e}")
        return False

@app.route('/data', methods=['POST'])
def get_gesture_data():
    data = request.get_json()
    
    # --- Валідація вхідних даних ---
    if not data or 'gesture_data' not in data or not data['gesture_data']:
        print("ПОМИЛКА: Неправильний формат даних або порожній масив 'gesture_data'")
        return jsonify({"error": "Bad Request: Invalid format or empty 'gesture_data' array"}), 400
    
    sequence_data = data['gesture_data']

    # Перевірка, що кожен запис має правильну кількість ознак (39)
    if len(sequence_data[0]) != EXPECTED_COLUMNS:
        msg = f"ПОМИЛКА: Очікувалось {EXPECTED_COLUMNS} колонок, а отримано {len(sequence_data[0])}"
        print(msg)
        return jsonify({"error": f"Bad Request: Expected {EXPECTED_COLUMNS} columns, but got {len(sequence_data[0])}"}), 400
        
    df = pd.DataFrame(sequence_data)
    
    # --- Приведення даних до єдиної довжини ---
    df_resampled = resample_sequence(df, SEQUENCE_LENGTH)
    
    if model and scaler and classes is not None:
        # --- РЕЖИМ РОЗПІЗНАВАННЯ (за новою логікою) ---
        try:
            # 1. Перетворюємо дані в numpy масив
            input_data = df_resampled.values.astype(float)
            
            # 2. Масштабуємо дані за допомогою завантаженого скейлера
            data_scaled = scaler.transform(input_data)
            
            # 3. Додаємо "batch" вимір для моделі: (75, 39) -> (1, 75, 39)
            data_for_model = np.expand_dims(data_scaled, axis=0)
            
            # 4. Робимо передбачення
            prediction_probs = model.predict(data_for_model, verbose=0)
            
            # 5. Інтерпретуємо результат
            label_index = np.argmax(prediction_probs)
            predicted_label = classes[label_index]
            confidence = np.max(prediction_probs)
            
            print(f"РОЗПІЗНАНО ЖЕСТ: {predicted_label} (впевненість: {confidence*100:.2f}%)")
            
            # Повертаємо результат у JSON форматі
            return jsonify({
                "prediction": predicted_label,
                "confidence": float(confidence) # Конвертуємо numpy.float32 в звичайний float
            }), 200
            
        except Exception as e:
            print(f"ПОМИЛКА ПРИ РОЗПІЗНАВАННІ: {e}")
            return jsonify({"error": "Internal Server Error during prediction"}), 500
    else:
        # --- РЕЖИМ ЗБОРУ ДАНИХ (логіка не змінилась) ---
        print("Сервер в режимі збору даних, модель не завантажена")
        print(f"Отримано жест з {len(df)} записів, нормалізовано до {len(df_resampled)}")
        
        label = input("Введіть назву жесту: ").strip().lower()
        
        if not label:
            print("ПОМИЛКА: Порожня назва жесту, дані не збережено")
        else:
            data_dir = "gesture_data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            i = 1
            while os.path.exists(f"{data_dir}/{label}_{i}.csv"):
                i += 1
                
            filepath = f"{data_dir}/{label}_{i}.csv"
            df_resampled.to_csv(filepath, index=False)
            
            print(f"Нормалізовані дані збережено у файл: {filepath}")
            
        return jsonify({"status": "Data saved for training"}), 200

if __name__ == '__main__':
    load_ai_components()
    app.run(host='0.0.0.0', port=5000, debug=True)