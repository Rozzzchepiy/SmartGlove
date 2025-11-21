import serial
import json
import threading
import tkinter as tk
from datetime import datetime
import time

SERIAL_PORT = 'COM15'
BAUD_RATE = 115200
TOTAL_AXES = 18

data_buffer = []
recording = False
ser = None
lock = threading.Lock()   # захист доступу до буфера

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
            time.sleep(0.001)  # не навантажує CPU
            continue

        # пишемо лише коли recording = True
        if recording:
            sample = parse_line(line)
            if sample:
                with lock:
                    data_buffer.append(sample)

        # Якщо ESP32 посилає END (не обов'язково)
        if line == "END":
            pass  # не зберігаємо тут, щоб не ламати логіку STOP

def save_data():
    with lock:
        if not data_buffer:
            print("No data to save.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sensor_data_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(data_buffer, f, indent=4)
        
        print(f"Data saved to {filename} ({len(data_buffer)} samples)")

def start_recording():
    global recording
    with lock:
        data_buffer.clear()
    recording = True
    print("Recording started")
    ser.write(b'START\n')

def stop_recording():
    global recording
    recording = False
    print("Stopping...")
    ser.write(b'STOP\n')

    # даємо ESP32 час на надсилання останніх ліній
    time.sleep(0.3)

    save_data()

    with lock:
        data_buffer.clear()
    print("Recording stopped and data saved.")

# GUI
root = tk.Tk()
root.title("MPU Recorder")

start_btn = tk.Button(root, text="Start Recording", command=start_recording)
start_btn.pack(padx=20, pady=10)

stop_btn = tk.Button(root, text="Stop Recording", command=stop_recording)
stop_btn.pack(padx=20, pady=10)

# Відкриття порту
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Потік читання UART
thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

root.mainloop()
