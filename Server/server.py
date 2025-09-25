import os
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify


# Який має приходити пакет даних по hhtp від Esp32
SEQUENCE_LENGTH = 75

MODEL_NAME = "model.pkl"

# Річ, яка приведе до однакових діапазонів значень з гіроскопа та акселерометра
SCALER_NAME = "scaler.pkl"

app = Flask(__name__)

model = None
scaler = None



# Або завантажуємо модель та скалер, якщо їх немає, то сервер в режимі збору даних
def load_model():
    global model
    global scaler
    
    try:
        if os.path.exists(MODEL_NAME) and os.path.isfile(MODEL_NAME):
            scaler = joblib.load(SCALER_NAME)
            print("Скалер завантажено")
            
            model = joblib.load(MODEL_NAME)
            print("Модель завантажена, сервер в режимі розпізнавання")
            return True
        else:
            print("Модель не знайдена, сервер в ЗБОРУ ДАНИХ")
            return False
    except Exception as e:
        print(f"Помилка завантаження моделі: {e}")
        return False

@app.route('/data', methods=['POST'])
def get_gesture_data():
    data = request.get_json()
    
    if not data or 'gesture_data' not in data or len(data['gesture_data']) != SEQUENCE_LENGTH:
        print("ПОМИЛКА: Неправильний формат даних")
        return "Bad Request", 400
    sequence_data = data['gesture_data']
    
    df = pd.DataFrame(sequence_data)
    
    if model and scaler:
        try:
            
            # Перетворюємо в (1, 75, 6) для моделі
            X_new = np.array([df.values]) 
            
            X_new_scaled = scaler.transform(X_new)
            prediction = model.predict(X_new_scaled)[0]
            
            print(f"РОЗПІЗНАНО ЖЕСТ: {prediction}")
            
        except Exception as e:
            print(f"ПОМИЛКА ПРИ РОЗПІЗНАВАННІ: {e}")
            return "Internal Server Error", 500
    else:
        print("Сервер в режимі збору даних, модель не завантажена")
        print("Отримані дані")
        
        label = input("Введіть назву жесть: ").strip().lower()
        
        if not label:
            print("ПОМИЛКА: Порожня назва жесту")
        else:
            data_dir = "gesture_data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            i = 1
            while os.path.exists(f"{data_dir}/{label}_{i}.csv"):
                i += 1
                
            filepath = f"{data_dir}/{label}_{i}.csv"
            df.to_csv(filepath, index=False)
            
            print(f"Дані збережено у файл: {filepath}")
            
    return "OK", 200

if __name__ == '__main__':
    load_model()
    app.run(host='0.0.0.0', port=5000, debug=True)