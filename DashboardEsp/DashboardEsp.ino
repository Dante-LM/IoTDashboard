#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

const char* ssid = "TP-Link_Guest_889D";
const char* password = "DashboardWifi";
const char* mqtt_server = "192.168.0.177";

WiFiClient vanieriot;
PubSubClient client(vanieriot);

constexpr uint8_t RST_PIN = D3;     // Configurable, see typical pin layout above
constexpr uint8_t SS_PIN = D4;     // Configurable, see typical pin layout above
MFRC522 rfid(SS_PIN, RST_PIN); // Instance of the class
MFRC522::MIFARE_Key key;
String tag;


void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected - ESP-8266 IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");

    // Attempt to connect
      if (client.connect("vanieriot")) {

        Serial.println("connected");  
        client.subscribe("SmartHome/Dashboard");
    } else {
        Serial.print("failed, rc=");
        Serial.print(client.state());
        Serial.println(" try again in 5 seconds");
        // Wait 5 seconds before retrying
        delay(5000);
    }
  }
}

String valueString;
void setup() {
  Serial.begin(9600);
  
  SPI.begin(); // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522
  
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void readLight(){

  int value = analogRead(A0);
  valueString = String(value);
  int str_len = valueString.length()+1;
  char value_array[str_len];
  valueString.toCharArray(value_array, str_len);
  client.publish("SmartHome/Dashboard", value_array);
  valueString = "";
  
  Serial.println("Analog Value: ");
  Serial.println(value);
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }
  if(!client.loop())
    client.connect("vanieriot");
    
//  readLight();

  if (!rfid.PICC_IsNewCardPresent())
      return;
  if (rfid.PICC_ReadCardSerial()) {
    for (byte i = 0; i < 4; i++) {
      tag += rfid.uid.uidByte[i];
    }
    Serial.println(tag);
    tag = "";
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }
    
    delay(3000);
}
