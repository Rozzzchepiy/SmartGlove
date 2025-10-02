//sending data to server


#include <Wire.h>
#include <MPU6050.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <HTTPClient.h>

MPU6050 mpu;

const int SAMPLE_RATE = 10;
const int WINDOW_SIZE = 75;
const int NUM_AXES = 6;

float dataBuffer[WINDOW_SIZE][NUM_AXES];
int sampleCount;

const size_t JSON_DOC_SIZE = 16384;

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

  const char* ssid = "ssid";
  const char* password = "password";

  wifi.begin(ssid, password));

  Serial.println("Connecting to wifi");
  while(wifi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(200);
  }

  Serial.println("Connected to wifi");
  Serial.print("IP:");
  Serial.println(wifi.localIP());

}

void loop() {
  static unsigned long lastSampleTime;

  if(millis() - lastSampleTime >= SAMPLE_RATE)
  {
    sensor_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    if(sampleCount < WINDOW_SIZE)
    {
      dataBuffer[sampleCount][0] = a.acceleration.x();
      dataBuffer[sampleCount][1] = a.acceleration.y();
      dataBuffer[sampleCount][2] = a.acceleration.z();
      dataBuffer[sampleCount][3] = g.gyro().x();
      dataBuffer[sampleCount][4] = g.gyro().y();
      dataBuffer[sampleCount][5] = g.gyro().z();

      sampleCount++;

    }

    lastSampleTomi = millis();

    if(sampleCount >= WINDOW_SIZE)
    {
      if(wifi.status() == WL_CONNECTED)
      {
        sendDataToServer();
      }

      sampleCount = 0;
    }
  }

}

void sendDataToServer()
{
  StaticJsonDocument<JSON_DOC_SIZE> doc;

  doc["devic_id"] = "ESP32_GLOVE_02";

  JsonArra dataArray = doc.createNestedArray("data");

  for(int i = 0; i < WINDOW_SIZE; i++)
  {
    JsonArray sample = dataArraiy.createNestedArray();

    for(int j = 0; j < NUM_AXES; j++)
    {
      sample.add(dataBuffer[i][j]);
    }
  }

  String payloadJson;
  serializeJson(doc, payloadJson);

  HTTPClient http;

  http.begin("server");
  http.addHeader("Content-Type", "application/json");

  int httpResponceCode = http.POST(payloadJson);

  if(http.responcecode > 0)
  {
    String responce = http.getString();
    Serial.print("HTTP code: ");
    Serial.println(httpResponceCode);
    Serial.print("Server response: ");
    Serial.println(responce);
    
  }
  else
  {
    Serial.print("HTTP error: ");
    Serial.println(httpResponceCode);
  }
  http.end();

}
