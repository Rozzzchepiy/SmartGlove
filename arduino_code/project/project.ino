//base code for testing mpu6050 with esp32
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  Serial.println("Initializing MPU6050");
  if(!mpu.begin(MPU6050_SCALE_2000DPS, MPU6050_RANGE_2G )){
    Serial.println("Can not found MPU6050-------Check the connection-------");
    while(true);
  }
  mpu.calibrateGyro();
  mpu.setThreshold();

}

void loop() {
  Vector rawAccel = mpu.readRawAccel();
  Vector rawGyro = mpu.readRawGyro();

  Serial.print("ax: "); Serial.print(rawAccel.XAxis);
  Serial.print(" | ay: "); Serial.print(rawAccel.YAxis);
  Serial.print(" | az: "); Serial.print(rawAccel.ZAxis);

  Serial.print(" || gx: "); Serial.print(rawGyro.XAxis);
  Serial.print(" | gy: "); Serial.print(rawGyro.YAxis);
  Serial.print(" | gz: "); Serial.println(rawGyro.ZAxis);

  Serial.println("----------------------------")
  delay(200);

}
