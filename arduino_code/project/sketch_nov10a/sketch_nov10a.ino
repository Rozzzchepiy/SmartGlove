#include <Wire.h>

// -------------------
// Адреси MPU
// -------------------
#define MPU1_ADDR 0x68
#define MPU2_ADDR 0x69
#define MPU3_ADDR 0x69  // на Wire1

// -------------------
// Читання MPU
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

// -------------------
// Ініціалізація MPU
// -------------------
void initMPU(TwoWire &bus, uint8_t addr) {
  bus.beginTransmission(addr);
  bus.write(0x6B); // PWR_MGMT_1
  bus.write(0x00); // wake up
  bus.endTransmission();
  delay(10);
}

// -------------------
// Setup
// -------------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(21, 22); // SDA, SCL
  Wire1.begin(18, 19); // SDA, SCL

  initMPU(Wire, MPU1_ADDR);
  initMPU(Wire, MPU2_ADDR);
  initMPU(Wire1, MPU3_ADDR);

  Serial.println("3 MPU6050 ready for testing.");
}

// -------------------
// Loop
// -------------------
void loop() {
  int16_t ax, ay, az, gx, gy, gz;

  // MPU1
  if (readMPU(Wire, MPU1_ADDR, ax, ay, az, gx, gy, gz))
    Serial.printf("MPU1   Acc: %d,%d,%d   Gyro: %d,%d,%d\n", ax,ay,az,gx,gy,gz);
  else
    Serial.println("MPU1 ERROR");

  // MPU2
  if (readMPU(Wire, MPU2_ADDR, ax, ay, az, gx, gy, gz))
    Serial.printf("MPU2   Acc: %d,%d,%d   Gyro: %d,%d,%d\n", ax,ay,az,gx,gy,gz);
  else
    Serial.println("MPU2 ERROR");

  // MPU3
  if (readMPU(Wire1, MPU3_ADDR, ax, ay, az, gx, gy, gz))
    Serial.printf("MPU3   Acc: %d,%d,%d   Gyro: %d,%d,%d\n", ax,ay,az,gx,gy,gz);
  else
    Serial.println("MPU3 ERROR");

  Serial.println("------------------------");
  delay(500);
}
