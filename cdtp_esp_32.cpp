#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "MAX30100_PulseOximeter.h"
#include "BluetoothSerial.h"

// --- AYARLAR ---
#define BUTON_PIN 15
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

// Limitler
float DUSME_HASSASIYETI = 18.0;     
const float HAREKET_ESIGI = 3.0;     
unsigned long SURE_DUSME_SONRASI = 60000;    
int NABIZ_ALT_LIMIT = 40;
int NABIZ_UST_LIMIT = 120; // 100 yerine 120 daha gerçekçi bir sýnýrdýr

// --- NESNELER ---
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_MPU6050 mpu;
PulseOximeter pox;
BluetoothSerial SerialBT;

// --- KONTROL DEÐÝÞKENLERÝ ---
bool sensorVarMi = false;        
uint32_t tsLastReport = 0;       
uint32_t tsLastBTData = 0; // Uygulama veri zamanlayýcýsý
bool dusmeModu = false;          
unsigned long dusmeZamani = 0; 
unsigned long sonHareketZamani = 0; 
String gelenKomut = ""; 

void onBeatDetected() { }

void setup() {
  setCpuFrequencyMhz(80); 
  Serial.begin(115200);
  pinMode(BUTON_PIN, INPUT_PULLUP);

  // Bluetooth ismi uygulama üzerinden bu þekilde görünür
  SerialBT.begin("Akilli_Bileklik_V6"); 

  Wire.begin();
  Wire.setTimeOut(50); 

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { Serial.println("OLED Hata"); }
  display.clearDisplay();
  display.display();

  if (!mpu.begin()) { Serial.println("MPU6050 Hata"); }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

  if (pox.begin()) {
    sensorVarMi = true;
    pox.setIRLedCurrent(MAX30100_LED_CURR_17_4MA);
    pox.setOnBeatDetectedCallback(onBeatDetected);
  }
  sonHareketZamani = millis();
}

void loop() {
  if (sensorVarMi) pox.update();

  // --- 1. BUTON VE MANUEL ACÝL DURUM ---
  if (digitalRead(BUTON_PIN) == LOW) { 
      delay(50); 
      if (digitalRead(BUTON_PIN) == LOW) {
          SerialBT.println("ALERT:PANIK_BUTONU"); // Uygulamaya özel kod
          display.clearDisplay();
          display.setTextColor(WHITE);
          display.setTextSize(2); display.setCursor(15, 25); display.println("PANIK!");
          display.display();
          while(digitalRead(BUTON_PIN) == LOW) { if (sensorVarMi) pox.update(); delay(10); }
      }
  }

  // --- 2. UYGULAMAYA VERÝ AKTARIMI (Her 1 Saniyede Bir) ---
  if (millis() - tsLastBTData > 1000) {
      if (sensorVarMi) {
          float hr = pox.getHeartRate();
          int spo2 = pox.getSpO2();
          String durum = dusmeModu ? "ACIL" : "NORMAL";

          // Uygulama için veri paketi: DATA:BPM:SPO2:DURUM
          SerialBT.printf("DATA:%d:%d:%s\n", (int)hr, spo2, durum.c_str());

          // Kritik Nabýz Uyarýlarýný Uygulamaya Gönder
          if (hr > 0) {
              if (hr > NABIZ_UST_LIMIT) SerialBT.println("ALERT:YUKSEK_NABIZ");
              if (hr < NABIZ_ALT_LIMIT) SerialBT.println("ALERT:DUSUK_NABIZ");
          }
      }
      tsLastBTData = millis();
  }

  // --- 3. DÜÞME TAKÝBÝ VE EKRAN ---
  if (millis() - tsLastReport > 300) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    float ivme = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));
    
    if (abs(ivme - 9.81) > HAREKET_ESIGI) { sonHareketZamani = millis(); }

    display.clearDisplay();

    if (!dusmeModu) {
      if (ivme > DUSME_HASSASIYETI) {
        dusmeModu = true;
        dusmeZamani = millis();
        SerialBT.println("ALERT:DUSME_ALGILANDI"); 
      }
      
      display.setTextColor(WHITE);
      display.setTextSize(1); display.setCursor(0,0); display.println("SAGLIK TAKIP");
      display.drawLine(0, 10, 128, 10, WHITE);
      display.setCursor(0, 20); display.print("Nabiz: "); display.setTextSize(2); display.print((int)pox.getHeartRate());
      display.setTextSize(1); display.setCursor(0, 45); display.print("Oksijen: %"); display.print(pox.getSpO2());
    } 
    else {
      // --- GERÝ SAYIM EKRANI ---
      unsigned long gecen = millis() - dusmeZamani;
      long kalan = (SURE_DUSME_SONRASI - gecen) / 1000;

      if (gecen > 3000 && abs(ivme - 9.81) > HAREKET_ESIGI) {
        dusmeModu = false;
        SerialBT.println("STATUS:IYIYIM");
      }

      if (gecen > SURE_DUSME_SONRASI) {
        display.fillScreen(WHITE); display.setTextColor(BLACK);
        display.setTextSize(2); display.setCursor(15, 20); display.println("! ACIL !");
        SerialBT.println("ALERT:CEVAP_YOK");
      } else {
        display.setTextColor(WHITE);
        display.setTextSize(1); display.setCursor(10, 5); display.println("DUSME ALGILANDI");
        display.setTextSize(4); display.setCursor(40, 25); display.print(kalan);
        display.setTextSize(1); display.setCursor(15, 55); display.println("IPTAL: HAREKET ET");
      }
    }
    display.display();
    tsLastReport = millis();
  }
}


