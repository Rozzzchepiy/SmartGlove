import serial
import json
import threading
import tkinter as tk
from datetime import datetime

SERIAL_PORT = 'COM15'
BAUD_RATE = 115200
TOTAL_AXES = 18

data_buffer = []
recording = False
ser = None  # глобальний об'єкт серійного порту

def parse_line(line):
    try:
        values = list(map(float, line.strip().split(',')))
        if len(values) != TOTAL_AXES:
            return None
        return values
    except:
        return None

def read_serial():
    global data_buffer, recording, ser
    while True:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue
        if recording:
            sample = parse_line(line)
            if sample:
                data_buffer.append(sample)
        # Якщо ESP32 відправляє END після STOP
        if line == "END" and recording:
            save_data()
            data_buffer.clear()

def save_data():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sensor_data_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data_buffer, f, indent=4)
    print(f"Data saved to {filename} ({len(data_buffer)} samples)")

def start_recording():
    global recording
    data_buffer.clear()  # очищаємо попередні дані перед новим записом
    recording = True
    print("Recording started")
    ser.write(b'START\n')  # надсилаємо команду ESP32

def stop_recording():
    global recording
    recording = False
    print("Recording stopped")
    ser.write(b'STOP\n')  # надсилаємо команду ESP32
    save_data()
    data_buffer.clear()

# GUI
root = tk.Tk()
root.title("MPU Recorder")

start_btn = tk.Button(root, text="Start Recording", command=start_recording)
start_btn.pack(padx=20, pady=10)

stop_btn = tk.Button(root, text="Stop Recording", command=stop_recording)
stop_btn.pack(padx=20, pady=10)

# Відкриваємо серійний порт один раз
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Потік для серійного читання
thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

root.mainloop()
