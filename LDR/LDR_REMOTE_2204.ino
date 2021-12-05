// Serial.begin(x) set rate
// analogRead(pin) set pin
// Serial.print(val) print data to serial port
int led = 2;


void setup() {
  Serial.begin(9600);
  pinMode(led, OUTPUT);
}

void loop() {
  int value = analogRead(A0);
  Serial.println("Analog Value: ");
  Serial.println(value);

  if (value < 900) {
    digitalWrite(led, HIGH);
  } else {
    digitalWrite(led, LOW);
  }
  delay(1000);
}
