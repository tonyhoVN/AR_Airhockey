#include <SoftwareSerial.h>

int RxData = 0;
int motorPin = 12;     

void setup() {
  Serial.begin(9600);
  Serial.begin(9600);
  pinMode(motorPin, OUTPUT);
  digitalWrite(motorPin, LOW);
}

void loop(){
  if (Serial.available()){
    RxData = Serial.read();
    if (RxData == '1'){
      digitalWrite(motorPin, HIGH);
     // analogWrite(motorPin, 255);
      delay(100);
    }

    if (RxData == '2'){
      digitalWrite(motorPin, HIGH);
      // analogWrite(motorPin, 255);
      delay(1500);
    }

    // RxData = '0';
  }

  digitalWrite(motorPin, LOW);
}