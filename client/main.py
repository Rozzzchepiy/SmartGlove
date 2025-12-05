import serial
import json
import threading
import tkinter as tk
import requests  
import time

# ==========================================
# НАЛАШТУВАННЯ
# ==========================================
SERIAL_PORT = 'COM4' 
BAUD_RATE = 115200

SERVER_URL = 'http://127.0.0.1:5000/data'

TOTAL_AXES = 18

data_buffer = []
is_collecting = False
ser = None

def parse_line(line):
    try:
        values = list(map(float, line.strip().split(',')))
        if len(values) != TOTAL_AXES:
            return None
        return values
    except:
        return None

def send_to_server():
    """Відправляє буфер даних на Flask сервер для розпізнавання"""
    global data_buffer
    
    if not data_buffer:
        print("Буфер порожній, нічого відправляти.")
        return

    print(f"Відправка {len(data_buffer)} записів на сервер...")
    
    # Формуємо JSON згідно вимог сервера
    payload = {"gesture_data": data_buffer}

    try:
        # Відправка POST запиту
        response = requests.post(SERVER_URL, json=payload, timeout=2)
        
        if response.status_code == 200:
            result = response.json()
            
            # Отримання відповіді
            gesture = result.get("prediction", "Невідомо")
            confidence = result.get("confidence", 0.0)
            
            print(f"ВІДПОВІДЬ СЕРВЕРА: {gesture} ({confidence*100:.1f}%)")
            
            # Оновлюємо текст у вікні програми
            lbl_result.config(text=f"ЖЕСТ: {gesture}\n({confidence*100:.1f}%)", fg="green")
        else:
            print(f"Помилка сервера: {response.status_code}")
            lbl_result.config(text=f"Помилка: {response.status_code}", fg="red")
            
    except requests.exceptions.ConnectionError:
        print("Не вдалося з'єднатися з сервером. Сервер запущено?")
        lbl_result.config(text="Сервер недоступний", fg="red")
    except Exception as e:
        print(f"Помилка: {e}")

    # Очищаємо буфер після відправки
    data_buffer.clear()

def read_serial():
    global is_collecting
    print(f"Підключення до {SERIAL_PORT}...")
    
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line: continue

                # Якщо ESP32 каже END, значить передача завершена - відправляємо на сервер
                if line == "END":
                    print("Отримано сигнал END. Обробка...")
                    send_to_server()
                    is_collecting = False
                    # Повертаємо колір кнопки назад
                    status_indicator.config(bg="gray")
                    continue

                if is_collecting:
                    sample = parse_line(line)
                    if sample:
                        data_buffer.append(sample)
                        
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(2)

def start_recording():
    global is_collecting
    data_buffer.clear()
    is_collecting = True
    
    lbl_result.config(text="Запис...", fg="black")
    status_indicator.config(bg="#00ff00") 
    
    print("--> Sending START")
    try:
        ser.write(b'START\n')
    except:
        print("Помилка відправки команди")

def stop_recording():
    # Ми не зупиняємо запис тут, ми просто кажемо ESP32 "Досить"
    # і чекаємо поки вона скине дані і скаже END
    print("--> Sending STOP")
    try:
        ser.write(b'STOP\n')
    except:
        print("Помилка відправки команди")

root = tk.Tk()
root.title("Gesture Client")
root.geometry("350x300")

# Індикатор статусу
status_indicator = tk.Label(root, width=5, bg="gray")
status_indicator.pack(pady=5)

lbl_info = tk.Label(root, text=f"Port: {SERIAL_PORT} -> Server: Localhost", fg="gray")
lbl_info.pack()

btn_start = tk.Button(root, text="ПОЧАТИ ЗАПИС (START)", command=start_recording, 
                      bg="#ddffdd", font=("Arial", 12, "bold"), height=2)
btn_start.pack(fill='x', padx=20, pady=10)

btn_stop = tk.Button(root, text="СТОП І ВІДПРАВИТИ", command=stop_recording, 
                     bg="#ffdddd", font=("Arial", 12, "bold"), height=2)
btn_stop.pack(fill='x', padx=20, pady=5)

lbl_result = tk.Label(root, text="Очікування...", font=("Helvetica", 18, "bold"), fg="blue")
lbl_result.pack(pady=20)

# Підключення до порту
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    thread = threading.Thread(target=read_serial, daemon=True)
    thread.start()
except Exception as e:
    lbl_result.config(text="Помилка порту!", fg="red")
    print(f"Не можу відкрити порт {SERIAL_PORT}. Перевір налаштування Bluetooth!")

root.mainloop()