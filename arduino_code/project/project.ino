#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include <Adafruit_HMC5883_U.h>

#include "libraries/I2Cdev/I2Cdev.h"
#include "libraries/MPU6050/MPU6050.h"


extern TwoWire Wire1;

MPU6050 mpu1(0x68, &Wire); 
MPU6050 mpu2(0x69, &Wire); 
MPU6050 mpu3(0x68, &Wire1);
MPU6050 mpu4(0x69, &Wire1);

Adafruit_HMC5883_Unified magnetometer = Adafruit_HMC5883_Unified(12345);

const char* WIFI_SSID = "wifi_network";
const char* WIFI_PASS = "wifi_pasword";
const char* SERVER_URL = "127.0.0.1"; 

const bool IS_TRAINING_MODE = true; 

const int BUTTON_PIN = 32;
const int TOTAL_AXES = 27;
const int SAMPLE_RATE_MS = 10; 
const int WINDOW_SIZE = 100;
const size_t JSON_DOC_SIZE = 16384; 

enum State { IDLE, RECORDING, SENDING };
State currentState = IDLE;

float data_buffer[WINDOW_SIZE][TOTAL_AXES]; 
int sample_count = 0; 
unsigned long last_sample_time = 0;

void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS); 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
}

void readAllSensors(float data_row[]) {

  int16_t ax, ay, az, gx, gy, gz;
  int axis_index = 0;
  sensors_event_t event;
  
  //mpu1
  mpu1.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  data_row[axis_index++] = (float)ax;
  data_row[axis_index++] = (float)ay;
  data_row[axis_index++] = (float)az;
  data_row[axis_index++] = (float)gx;
  data_row[axis_index++] = (float)gy;
  data_row[axis_index++] = (float)gz;

  //mpu2
  mpu2.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  data_row[axis_index++] = (float)ax;
  data_row[axis_index++] = (float)ay;
  data_row[axis_index++] = (float)az;
  data_row[axis_index++] = (float)gx;
  data_row[axis_index++] = (float)gy;
  data_row[axis_index++] = (float)gz;
  
  //mpu3
  mpu3.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  data_row[axis_index++] = (float)ax;
  data_row[axis_index++] = (float)ay;
  data_row[axis_index++] = (float)az;
  data_row[axis_index++] = (float)gx;
  data_row[axis_index++] = (float)gy;
  data_row[axis_index++] = (float)gz;

  //mpu4
  mpu4.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  data_row[axis_index++] = (float)ax;
  data_row[axis_index++] = (float)ay;
  data_row[axis_index++] = (float)az;
  data_row[axis_index++] = (float)gx;
  data_row[axis_index++] = (float)gy;
  data_row[axis_index++] = (float)gz;

  //magnetometer
  magnetometer.getEvent(&event);
  data_row[axis_index++] = event.magnetic.x; 
  data_row[axis_index++] = event.magnetic.y;
  data_row[axis_index++] = event.magnetic.z;
  
  
  
}

void sendDataToServer() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }
  
  StaticJsonDocument<JSON_DOC_SIZE> doc;
  
  doc["device_id"] = "SMART_GLOVE_ESP32"; 
  doc["mode"] = (IS_TRAINING_MODE) ? "TRAINING" : "RECOGNITION";
  doc["sample_count"] = sample_count; 
  
  JsonArray data_array = doc.createNestedArray("data");
  for (int i = 0; i < sample_count; i++) { // Використовуємо sample_count
    JsonArray sample = data_array.createNestedArray();
    for (int j = 0; j < TOTAL_AXES; j++) {
      sample.add(data_buffer[i][j]); 
    }
  }

  String payload_json;
  serializeJson(doc, payload_json);
  
  HTTPClient http;
  http.begin(SERVER_URL); 
  http.addHeader("Content-Type", "application/json"); 
  
  int httpResponseCode = http.POST(payload_json);
  
  if (httpResponseCode > 0) {
    Serial.println("Success! Response: " + http.getString());
  } else {
    Serial.println("HTTP Error: " + String(httpResponseCode));
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(); 
  Wire1.begin(19, 18); 
  
  pinMode(BUTTON_PIN, INPUT_PULLDOWN); 
  

  connectWiFi();
  Serial.println("System initialized. Current mode: " + String((IS_TRAINING_MODE) ? "TRAINING" : "RECOGNITION"));
  Serial.println("Press button to START recording.");
}

void loop() {
  static unsigned long last_sample_time = 0;
  int buttonState = digitalRead(BUTTON_PIN);
  
  if (buttonState == HIGH) {
    delay(20);
    if (digitalRead(BUTTON_PIN) == HIGH) {
        
      if (currentState == IDLE) {
        sample_count = 0;
        currentState = RECORDING;
        Serial.println(">>> RECORDING STARTED <<<");
        
      } else if (currentState == RECORDING) {
        currentState = SENDING;
        Serial.print(">>> RECORDING STOPPED. Samples collected: ");
        Serial.println(sample_count);
      }
      
      while(digitalRead(BUTTON_PIN) == HIGH); 
    }
  }
  
  if (currentState == RECORDING && (millis() - last_sample_time >= SAMPLE_RATE_MS)) {
    
    if (sample_count < WINDOW_SIZE) {
      readAllSensors(data_buffer[sample_count]);
      sample_count++;
      Serial.print("Sample: "); Serial.println(sample_count);
    } else {
      currentState = SENDING;
      Serial.println("!!! WINDOW FULL. AUTO-SENDING !!!");
    }
    last_sample_time = millis();
  }

  if (currentState == SENDING) {
    Serial.println("--- Sending Data to Server ---");
    sendDataToServer();
    
    currentState = IDLE; 
    Serial.println("Cycle complete. System is now IDLE. Press button to START again.");
  }
}