#include <Arduino.h>

const int LED_Pin = D8;

void setup() {
  pinMode(LED_Pin, OUTPUT);
}

void loop() {
  digitalWrite(LED_Pin, HIGH);
  delay(1000);
  digitalWrite(LED_Pin, LOW);
  delay(1000);
}
