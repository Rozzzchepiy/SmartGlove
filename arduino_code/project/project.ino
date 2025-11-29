#include <Wire.h>
#include "BluetoothSerial.h"

BluetoothSerial SerialBT; // Створюємо об'єкт Bluetooth

// -------------------
// Адреси MPU
// -------------------
#define MPU1_ADDR 0x68
#define MPU2_ADDR 0x69
#define MPU3_ADDR 0x69 // на Wire1

const int TOTAL_AXES = 18;
const int WINDOW_SIZE = 1000;
const int SAMPLE_RATE_MS = 10;

enum State { IDLE, RECORDING, SENDING };
State currentState = IDLE;

// Буфер даних
float data_buffer[WINDOW_SIZE][TOTAL_AXES];
int sample_count = 0;
unsigned long last_sample_time = 0;

// Функції MPU (скорочено для економії місця, логіка та ж)
bool readMPU(TwoWire &bus, uint8_t addr, int16_t &ax, int16_t &ay, int16_t &az, int16_t &gx, int16_t &gy, int16_t &gz) {
  bus.beginTransmission(addr); bus.write(0x3B);
  if (bus.endTransmission(false) != 0) return false;
  bus.requestFrom(addr, (uint8_t)14);
  if (bus.available() < 14) return false;
  ax = (bus.read() << 8) | bus.read(); ay = (bus.read() << 8) | bus.read(); az = (bus.read() << 8) | bus.read();
  bus.read(); bus.read();
  gx = (bus.read() << 8) | bus.read(); gy = (bus.read() << 8) | bus.read(); gz = (bus.read() << 8) | bus.read();
  return true;
}

void initMPU(TwoWire &bus, uint8_t addr) {
  bus.beginTransmission(addr); bus.write(0x6B); bus.write(0x00); bus.endTransmission(); delay(10);
}

void readAllSensors(float data_row[]) {
  int16_t ax, ay, az, gx, gy, gz;
  int idx = 0;
  // Якщо датчик не відповідає, пишемо 0, щоб не зміщувати стовпці CSV
  if(readMPU(Wire, MPU1_ADDR, ax, ay, az, gx, gy, gz)) { data_row[idx++] = ax; data_row[idx++] = ay; data_row[idx++] = az; data_row[idx++] = gx; data_row[idx++] = gy; data_row[idx++] = gz; } else { idx+=6; }
  if(readMPU(Wire, MPU2_ADDR, ax, ay, az, gx, gy, gz)) { data_row[idx++] = ax; data_row[idx++] = ay; data_row[idx++] = az; data_row[idx++] = gx; data_row[idx++] = gy; data_row[idx++] = gz; } else { idx+=6; }
  if(readMPU(Wire1, MPU3_ADDR, ax, ay, az, gx, gy, gz)) { data_row[idx++] = ax; data_row[idx++] = ay; data_row[idx++] = az; data_row[idx++] = gx; data_row[idx++] = gy; data_row[idx++] = gz; } else { idx+=6; }
}

void sendData() {
  Serial.println("Bluetooth: Sending data...");
  for (int i = 0; i < sample_count; i++) {
    for (int j = 0; j < TOTAL_AXES; j++) {
      SerialBT.print(data_buffer[i][j]);
      if (j < TOTAL_AXES - 1) SerialBT.print(',');
    }
    SerialBT.print('\n');
    
    // ВАЖЛИВО: Bluetooth повільніший за USB. Робимо паузу кожні 20 рядків.
    if (i % 20 == 0) delay(10);
  }
  SerialBT.println("END"); // Маркер кінця
  Serial.println("Bluetooth: Transfer complete.");
}

void setup() {
  Serial.begin(115200); // USB для відладки
  
  // Запуск Bluetooth. Ім'я пристрою "SmartGlove_ESP32"
  SerialBT.begin("SmartGlove_ESP32"); 
  Serial.println("Bluetooth Started! Pair with 'SmartGlove_ESP32'");

  Wire.begin(21, 22);
  Wire1.begin(18, 19);
  initMPU(Wire, MPU1_ADDR);
  initMPU(Wire, MPU2_ADDR);
  initMPU(Wire1, MPU3_ADDR);
}

void loop() {
  // Читаємо команди з Bluetooth
  if(SerialBT.available()) {
    String cmd = SerialBT.readStringUntil('\n');
    cmd.trim();
    if(cmd == "START") {
      currentState = RECORDING;
      sample_count = 0;
      Serial.println("CMD: START");
    } else if(cmd == "STOP") {
      currentState = SENDING;
      Serial.println("CMD: STOP");
    } else if(cmd == "RESET") {
       currentState = IDLE;
       sample_count = 0;
    }
  }

  // Запис даних
  if(currentState == RECORDING && millis() - last_sample_time >= SAMPLE_RATE_MS) {
    if(sample_count < WINDOW_SIZE) {
      readAllSensors(data_buffer[sample_count]);
      sample_count++;
    } else {
      currentState = SENDING; // Буфер повний
    }
    last_sample_time = millis();
  }

  // Відправка
  if(currentState == SENDING) {
    sendData();
    currentState = IDLE;
    sample_count = 0; // Очищення після відправки
  }
}