/*
  ESP32 Mixer Controller (HTTP server)
  - Connects to WiFi
  - POST /mix with JSON: {"red":%, "blue":%, "yellow":%, "white":%, "black":%}
  - Each base controls a relay (GPIO pins)
  - Duration computed from percentage of a batch (assume fixed ml/s per pump)
*/
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASS";

// Relay pins (adjust as needed)
const int PIN_RED = 14;
const int PIN_BLUE = 27;
const int PIN_YELLOW = 26;
const int PIN_WHITE = 25;
const int PIN_BLACK = 33;

// Pump calibration (ml per second)
float PUMP_MLPS_RED = 1.5;
float PUMP_MLPS_BLUE = 1.4;
float PUMP_MLPS_YELLOW = 1.6;
float PUMP_MLPS_WHITE = 1.8;
float PUMP_MLPS_BLACK = 1.3;

// Assume batch volume ml (change to grams density if needed)
float BATCH_ML = 100.0;

WebServer server(80);

void setupPins(){
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);
  pinMode(PIN_YELLOW, OUTPUT);
  pinMode(PIN_WHITE, OUTPUT);
  pinMode(PIN_BLACK, OUTPUT);
  digitalWrite(PIN_RED, LOW);
  digitalWrite(PIN_BLUE, LOW);
  digitalWrite(PIN_YELLOW, LOW);
  digitalWrite(PIN_WHITE, LOW);
  digitalWrite(PIN_BLACK, LOW);
}

void setup() {
  Serial.begin(115200);
  setupPins();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting WiFi");
  while(WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  Serial.print("WiFi OK: "); Serial.println(WiFi.localIP());

  server.on("/status", HTTP_GET, [](){
    server.send(200, "application/json", "{\"ok\":true}");
  });

  server.on("/mix", HTTP_POST, [](){
    if (!server.hasArg("plain")) {
      server.send(400, "application/json", "{\"ok\":false,\"error\":\"no body\"}");
      return;
    }
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, server.arg("plain"));
    if(err){
      server.send(400, "application/json", "{\"ok\":false,\"error\":\"bad json\"}");
      return;
    }
    float red = doc["red"] | 0;
    float blue = doc["blue"] | 0;
    float yellow = doc["yellow"] | 0;
    float white = doc["white"] | 0;
    float black = doc["black"] | 0;

    // convert % to ml
    float ml_red = BATCH_ML * (red/100.0);
    float ml_blue = BATCH_ML * (blue/100.0);
    float ml_yellow = BATCH_ML * (yellow/100.0);
    float ml_white = BATCH_ML * (white/100.0);
    float ml_black = BATCH_ML * (black/100.0);

    // durations
    unsigned long t_red = (unsigned long)(1000.0 * (ml_red / PUMP_MLPS_RED));
    unsigned long t_blue = (unsigned long)(1000.0 * (ml_blue / PUMP_MLPS_BLUE));
    unsigned long t_yellow = (unsigned long)(1000.0 * (ml_yellow / PUMP_MLPS_YELLOW));
    unsigned long t_white = (unsigned long)(1000.0 * (ml_white / PUMP_MLPS_WHITE));
    unsigned long t_black = (unsigned long)(1000.0 * (ml_black / PUMP_MLPS_BLACK));

    // simple sequential mixing (can be parallel if pumps independent)
    auto runPump = [](int pin, unsigned long ms){
      if(ms==0) return;
      digitalWrite(pin, HIGH);
      delay(ms);
      digitalWrite(pin, LOW);
    };

    runPump(PIN_WHITE, t_white);
    runPump(PIN_YELLOW, t_yellow);
    runPump(PIN_RED, t_red);
    runPump(PIN_BLUE, t_blue);
    runPump(PIN_BLACK, t_black);

    String resp = "{\"ok\":true,\"dur_ms\":{\"red\":" + String(t_red) +
                  ",\"blue\":" + String(t_blue) +
                  ",\"yellow\":" + String(t_yellow) +
                  ",\"white\":" + String(t_white) +
                  ",\"black\":" + String(t_black) + "}}";
    server.send(200, "application/json", resp);
  });

  server.begin();
}

void loop() {
  server.handleClient();
}
