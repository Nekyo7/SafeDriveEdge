void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("================================");
  Serial.println("ESP32 WORKING");
  Serial.println("Serial communication OK");
  Serial.println("================================");
}

void loop() {
  Serial.println("ESP32 is alive...");
  delay(1000);
}