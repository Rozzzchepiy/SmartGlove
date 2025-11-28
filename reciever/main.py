import serial
import json
import threading
import tkinter as tk
import keyboard
from datetime import datetime
import time
import requests

SERIAL_PORT = 'COM15'
BAUD_RATE = 115200
TOTAL_AXES = 18

SERVER_URL = "http://127.0.0.1:5000/data"   # <-- заміниш на свій IP коли буде ESP або інший ПК

data_buffer = []
recording = False
ser = None
lock = threading.Lock()


def parse_line(line):
    try:
        values = list(map(float, line.strip().split(',')))
        if len(values) != TOTAL_AXES:
            return None
        return values
    except:
        return None


def read_serial():
    global recording

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
        except:
            continue

        if not line:
            continue

        if recording:
            sample = parse_line(line)
            if sample:
                with lock:
                    data_buffer.append(sample)


def send_to_server(sequence):
    try:
        response = requests.post(
            SERVER_URL,
            json={"gesture_data": sequence},
            timeout=5
        )

        print("\n=== SERVER RESPONSE ===")
        print(response.text)
        print("=======================\n")

    except Exception as e:
        print("\nПОМИЛКА НАДСИЛАННЯ:", e, "\n")


def start_recording():
    global recording
    if recording:
        return
    with lock:
        data_buffer.clear()
    recording = True
    print("\n=== RECORDING STARTED ===\n")
    ser.write(b'START\n')


def stop_recording():
    global recording
    if not recording:
        return
    recording = False
    print("\n=== RECORDING STOPPED ===")
    ser.write(b'STOP\n')

    time.sleep(0.2)

    with lock:
        sequence = list(data_buffer)

    # --- ВІДПРАВКА НА СЕРВЕР ---
    if len(sequence) > 0:
        print(f"Надсилаю {len(sequence)} рядків на сервер…")
        send_to_server(sequence)

    with lock:
        data_buffer.clear()

    print("Готово до наступного запису.\n")


def listen_keyboard():
    print("ENTER = старт/стоп")

    while True:
        keyboard.wait("enter")
        if recording:
            stop_recording()
        else:
            start_recording()
        time.sleep(0.2)


# ---------------- MAIN ----------------

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

threading.Thread(target=read_serial, daemon=True).start()
threading.Thread(target=listen_keyboard, daemon=True).start()

root = tk.Tk()
root.title("MPU Recorder")

tk.Button(root, text="Start Recording", command=start_recording).pack(padx=20, pady=10)
tk.Button(root, text="Stop Recording", command=stop_recording).pack(padx=20, pady=10)

root.mainloop()
