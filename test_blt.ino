#include <SoftwareSerial.h>
# define LED 12
int state; 

// Setup bluetooth
SoftwareSerial BT(0,1);

void setup() {
  pinMode(LED, OUTPUT);
  BT.begin(9600);
  Serial.begin(9600);
}

void loop() {
  Serial.println(state);

  if (BT.available() > 0)
  {
    state = BT.read();
    if (state == '1') digitalWrite(LED, HIGH);
    delay(10);
  }

  if (Serial.available() > 0)
  {
    state = Serial.read();
    if (state == '1') digitalWrite(LED, HIGH);
    delay(10);
  }

  // Reset state
  state = '0';
  digitalWrite(LED, LOW);
}
