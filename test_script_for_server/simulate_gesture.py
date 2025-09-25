import requests
import json
import numpy as np
import time

# --- НАЛАШТУВАННЯ ---
SERVER_URL = "http://127.0.0.1:5000/data" # Адреса вашого локального сервера
SEQUENCE_LENGTH = 75 # Має збігатися з налаштуваннями сервера
NUM_FEATURES = 6     # ax, ay, az, gx, gy, gz

def generate_fake_gesture_data():
    """
    Генерує реалістично виглядаючі дані жесту.
    Наприклад, синусоїдальний рух по осі 'ax' і випадковий шум для інших.
    """
    gesture_list = []
    # Створюємо "хвилю" для імітації руху
    time_steps = np.linspace(0, 2 * np.pi, SEQUENCE_LENGTH)
    
    # Імітуємо жест "свайп"
    ax_wave = np.sin(time_steps) * 5 # Сильний рух по осі X
    az_wave = np.cos(time_steps) * 2 # Невеликий рух по осі Z
    
    for i in range(SEQUENCE_LENGTH):
        # Додаємо трохи випадкового шуму, щоб дані не були ідеальними
        sample = {
            "ax": ax_wave[i] + np.random.uniform(-0.5, 0.5),
            "ay": np.random.uniform(-1, 1),
            "az": az_wave[i] + np.random.uniform(-0.5, 0.5),
            "gx": np.random.uniform(-0.2, 0.2),
            "gy": np.random.uniform(-0.2, 0.2),
            "gz": np.random.uniform(-0.2, 0.2)
        }
        gesture_list.append(sample)
    return gesture_list

def send_gesture_to_server(gesture_data):
    """
    Відправляє згенеровані дані на сервер у форматі JSON.
    """
    headers = {'Content-Type': 'application/json'}
    payload = {"gesture_data": gesture_data}
    
    try:
        response = requests.post(SERVER_URL, data=json.dumps(payload), headers=headers)
        
        # Перевірка статусу відповіді
        if response.status_code == 200:
            print("Сервер відповів успішно:")
        else:
            print(f"Помилка! Сервер відповів зі статусом: {response.status_code}")
            print(f"Тіло відповіді: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"Помилка з'єднання: не вдалося підключитися до {SERVER_URL}")
        print("Переконайтесь, що сервер 'server.py' запущено.")

# --- Точка входу, аналог public static void main(String[] args) ---
if __name__ == "__main__":
    print("Генеруємо фейковий жест...")
    fake_data = generate_fake_gesture_data()
    
    print(f"Відправляємо жест на сервер: {SERVER_URL}")
    send_gesture_to_server(fake_data)