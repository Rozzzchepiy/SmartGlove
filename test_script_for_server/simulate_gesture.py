import requests
import json
import numpy as np
import random
import time

# --- НАЛАШТУВАННЯ ---
SERVER_URL = "http://127.0.0.1:5000/data" # Адреса вашого локального сервера


NUM_FEATURES = 39

# Діапазон для генерації випадкової довжини послідовності
MIN_GESTURE_LENGTH = 20
MAX_GESTURE_LENGTH = 150


def generate_fake_gesture_data(length: int):
    """
    Генерує випадкові дані жесту заданої довжини та з потрібною кількістю ознак.
    
    Args:
        length (int): Кількість записів (часових кроків) у жесті.
        
    Returns:
        list: Список списків, що представляє дані жесту.
    """
    # Створюємо 2D NumPy масив з випадковими значеннями від 0 до 1
    # Розмір: (length, NUM_FEATURES)
    gesture_array = np.random.rand(length, NUM_FEATURES)
    
    # Можна додати масштабування, щоб дані були схожі на реальні,
    # але для тестування структури це не обов'язково.
    # Наприклад: gesture_array *= 10
    
    # Перетворюємо NumPy масив у список списків, який легко серіалізується в JSON
    return gesture_array.tolist()

def send_gesture_to_server(gesture_data):
    """
    Відправляє згенеровані дані на сервер у форматі JSON.
    """
    headers = {'Content-Type': 'application/json'}
    # Структура payload має відповідати тій, яку очікує сервер
    payload = {"gesture_data": gesture_data}
    
    try:
        response = requests.post(SERVER_URL, data=json.dumps(payload), headers=headers)
        
        # Перевірка статусу відповіді
        if response.status_code == 200:
            print(f"Сервер успішно обробив запит (статус {response.status_code}).")
        else:
            print(f"ПОМИЛКА! Сервер відповів зі статусом: {response.status_code}")
            print(f"Тіло відповіді: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"\nПОМИЛКА З'ЄДНАННЯ: не вдалося підключитися до {SERVER_URL}")
        print("Переконайтесь, що сервер 'server.py' запущено і доступний за цією адресою.")

# --- Головний цикл для інтерактивного тестування ---
if __name__ == "__main__":
    print("--- Інтерактивний клієнт для тестування сервера жестів ---")
    print(f"Сервер: {SERVER_URL}")
    print(f"Кількість ознак за раз: {NUM_FEATURES}")
    print("-" * 55)

    while True:
        user_input = input("Натисніть Enter, щоб відправити тестовий жест, або введіть 'q' для виходу: ")
        if user_input.strip().lower() == 'q':
            print("Вихід.")
            break
            
        # Генеруємо випадкову довжину для послідовності
        random_length = random.randint(MIN_GESTURE_LENGTH, MAX_GESTURE_LENGTH)
        print(f"\nГенеруємо жест з випадковою довжиною: {random_length}...")
        
        # Створюємо фейкові дані
        fake_data = generate_fake_gesture_data(random_length)
        
        print(f"Відправляємо жест на сервер...")
        send_gesture_to_server(fake_data)
        print("-" * 55)