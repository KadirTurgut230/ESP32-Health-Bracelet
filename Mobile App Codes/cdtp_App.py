from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from threading import Thread
import time  # <--- CPU'yu dinlendirmek için ŞART!

import cdtp_main_panel
# Ayarlar paneli tamamen iptal edildiği için import etmiyoruz
# import cdtp_settings_panel 
import cdtp_comm

class MainApp(App):
    def build(self):
        self.sm = ScreenManager()
        
        # Sadece Ana Ekran var
        self.main_screen = cdtp_main_panel.MainScreen(name='main')
        self.sm.add_widget(self.main_screen)
        
        self.sm.current = 'main'
        return self.sm
    
    def on_start(self):
        # 1. İzinleri iste
        self.request_android_permissions()
        
        # 2. WakeLock al (Arka planda çalışması için)
        self.acquire_wakelock()
        
        # 3. Sistemi başlat
        Clock.schedule_once(self.delayed_start, 2)

    def delayed_start(self, dt):
        """Bluetooth dinleyicisini başlatır"""
        print("Sistem Başlatılıyor (Pasif Dinleme Modu)...")
        
        # ESP32 sürekli yayın yaptığı için bizim bir şey göndermemize gerek yok.
        # Sadece dinleme hattını açıyoruz.
        t = Thread(target=self.bluetooth_listener_thread, daemon=True)
        t.start()

    def bluetooth_listener_thread(self):
        """
        ESP32'den gelen verileri ayıklar.
        Formatlar:
        1. Veri:  DATA:NABIZ:SPO2:DURUM
        2. Alarm: ALERT:DUSME_ALGILANDI
        """
        while True:
            # cdtp_comm içindeki okuma fonksiyonu
            message = cdtp_comm.read_bluetooth_message()
            
            if message and message != "DISCONNECTED":
                message = message.strip()
                # SENARYO A: Acil Durum (ALERT: ile başlar)
                # Örn: ALERT:DUSME_ALGILANDI
                if 'DATA' in message:
                    self.update_ui_safe(message)

                elif 'STATUS' in message or 'ALERT' in message:
                    cdtp_comm.send_notification(message)

            else:
                # EĞER VERİ YOKSA İŞLEMCİYİ DİNLENDİR
                # Bu satır çok kritiktir. Olmazsa telefon donar/ısınır.
                time.sleep(0.1) 

    @mainthread
    def update_ui_safe(self, message):
        """Thread'den gelen veriyi ekrana basar"""
        try:
            self.main_screen.update_from_main(message)
        except Exception as e:
            print(f"UI Güncelleme Hatası: {e}")

    def acquire_wakelock(self):
        """Telefonun ekranı kapansa bile işlemcinin çalışmasını sağlar"""
        if platform == 'android':
            from jnius import autoclass
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                pm = PythonActivity.mActivity.getSystemService(Context.POWER_SERVICE)
                self.wakelock = pm.newWakeLock(1, "HealthTracker:WakeLock")
                self.wakelock.acquire()
                print("WakeLock Aktif.")
            except Exception as e:
                print(f"WakeLock Hatası: {e}")
        
    def request_android_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            permissions = [
                Permission.BLUETOOTH, Permission.BLUETOOTH_ADMIN,
                Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION,
                Permission.POST_NOTIFICATIONS, Permission.WAKE_LOCK
            ]
            try:
                permissions.append(Permission.BLUETOOTH_CONNECT)
                permissions.append(Permission.BLUETOOTH_SCAN)
            except: pass
            request_permissions(permissions)

    def on_stop(self):
        if hasattr(self, 'wakelock') and self.wakelock.isHeld():
            self.wakelock.release()

if __name__ == '__main__':
    MainApp().run()