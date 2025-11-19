#include <Wire.h>
#include "BluetoothSerial.h"

BluetoothSerial bluetooth;

// -------------------
// Адреси MPU
// -------------------
#define MPU1_ADDR 0x68
#define MPU2_ADDR 0x69
#define MPU3_ADDR 0x69  // на Wire1


// -------------------
// Параметри
// -------------------
const int TOTAL_AXES = 18;
const int WINDOW_SIZE = 200;
const int SAMPLE_RATE_MS = 10;

enum State { IDLE, RECORDING, SENDING };
State currentState = IDLE;

float data_buffer[WINDOW_SIZE][TOTAL_AXES];
int sample_count = 0;
unsigned long last_sample_time = 0;

// -------------------
// Функції для MPU
// -------------------
bool readMPU(TwoWire &bus, uint8_t addr,
             int16_t &ax, int16_t &ay, int16_t &az,
             int16_t &gx, int16_t &gy, int16_t &gz)
{
  bus.beginTransmission(addr);
  bus.write(0x3B); // ACCEL_XOUT_H
  if (bus.endTransmission(false) != 0) return false;

  bus.requestFrom(addr, (uint8_t)14);
  if (bus.available() < 14) return false;

  ax = (bus.read() << 8) | bus.read();
  ay = (bus.read() << 8) | bus.read();
  az = (bus.read() << 8) | bus.read();

  bus.read(); bus.read(); // temp

  gx = (bus.read() << 8) | bus.read();
  gy = (bus.read() << 8) | bus.read();
  gz = (bus.read() << 8) | bus.read();

  return true;
}

void initMPU(TwoWire &bus, uint8_t addr) {
  bus.beginTransmission(addr);
  bus.write(0x6B); // PWR_MGMT_1
  bus.write(0x00); // wake up
  bus.endTransmission();
  delay(10);
}

// -------------------
// Читання всіх MPU
// -------------------
void readAllSensors(float data_row[]) {
  int16_t ax, ay, az, gx, gy, gz;
  int idx = 0;

  if(readMPU(Wire, MPU1_ADDR, ax, ay, az, gx, gy, gz)) {
    data_row[idx++] = ax; data_row[idx++] = ay; data_row[idx++] = az;
    data_row[idx++] = gx; data_row[idx++] = gy; data_row[idx++] = gz;
  }

  if(readMPU(Wire, MPU2_ADDR, ax, ay, az, gx, gy, gz)) {
    data_row[idx++] = ax; data_row[idx++] = ay; data_row[idx++] = az;
    data_row[idx++] = gx; data_row[idx++] = gy; data_row[idx++] = gz;
  }

  if(readMPU(Wire1, MPU3_ADDR, ax, ay, az, gx, gy, gz)) {
    data_row[idx++] = ax; data_row[idx++] = ay; data_row[idx++] = az;
    data_row[idx++] = gx; data_row[idx++] = gy; data_row[idx++] = gz;
  }
}

// -------------------
// Відправка даних
// -------------------
void sendData() {
  for (int i = 0; i < sample_count; i++) {
    for (int j = 0; j < TOTAL_AXES; j++) {
      bluetooth.print(data_buffer[i][j]);
      if (j < TOTAL_AXES - 1) bluetooth.print(',');
    }
    bluetooth.print('\n');
  }
  bluetooth.println("END");
}

// -------------------
// Setup
// -------------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(21, 22);
  Wire1.begin(18, 19);

  initMPU(Wire, MPU1_ADDR);
  initMPU(Wire, MPU2_ADDR);
  initMPU(Wire1, MPU3_ADDR);

  bluetooth.begin("SmartGlove");
  Serial.println("System ready. Waiting for Bluetooth command...");
}

// -------------------
// Loop
// -------------------
void loop() {
  if(bluetooth.available()) {
    String cmd = bluetooth.readStringUntil('\n');
    cmd.trim();

    if(cmd == "START") {
      currentState = RECORDING;
      sample_count = 0;
      Serial.println("Recording started");
    } else if(cmd == "STOP") {
      currentState = SENDING;
      Serial.println("Recording stopped");
    }
  }

  if(currentState == RECORDING && millis() - last_sample_time >= SAMPLE_RATE_MS) {
    if(sample_count < WINDOW_SIZE) {
      readAllSensors(data_buffer[sample_count]);
      sample_count++;
    } else {
      currentState = SENDING;
      Serial.println("Buffer full — sending data");
    }
    last_sample_time = millis();
  }

  if(currentState == SENDING) {
    sendData();
    currentState = IDLE;
    Serial.println("Cycle complete — system idle");
  }
}
