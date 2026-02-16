from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import platform

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pulse_value = "--"
        self.oxygen_value = "--"
        
        # UI Kurulumu
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        # Ana Düzen (Orijinal ayarlar)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Arka Plan (Beyaz)
        with layout.canvas.before:
            Color(1, 1, 1, 1) 
            self.rect = Rectangle(size=Window.size, pos=layout.pos)
        layout.bind(pos=self.update_rect, size=self.update_rect)
        
        # 1. ÜST KISIM (Sadece CLOSE butonu kaldı)
        top_layout = BoxLayout(size_hint_y=0.1, height=70, spacing=10, padding=[0, 10, 0, 0])
        top_layout.add_widget(Label()) # Boşluk
        self.close_btn = Button(text='CLOSE', size_hint=(0.3, 1), background_color=(0.8, 0.1, 0.1, 1), bold=True)
        self.close_btn.bind(on_press=self.close_app)
        top_layout.add_widget(self.close_btn)
        layout.add_widget(top_layout)
        
        # 2. VERİ GÖSTERGELERİ (Yazı tipleri ve renkler orijinal haliyle korundu)
        # Butonlar gittiği için size_hint_y'yi artırarak ekranı kaplamasını sağladık
        data_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.9)
        
        # --- NABIZ KISMI ---
        pulse_container = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.5)
        pulse_container.add_widget(Label(text='HEART RATE', font_size='24sp', color=(0,0,0,1), bold=True, size_hint_y=None, height=40))
        # Orijinal font boyutu (64sp) ve rengi korundu
        self.pulse_output = Label(font_size='64sp', color=(0.2, 0.2, 0.8, 1), bold=True, size_hint_y=1)
        pulse_container.add_widget(self.pulse_output)
        data_layout.add_widget(pulse_container)
        
        # --- OKSİJEN KISMI ---
        oxygen_container = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.5)
        # Sadece başlık değişti (INMOBILITY -> OXYGEN RATE)
        oxygen_container.add_widget(Label(text='OXYGEN RATE', font_size='24sp', color=(0,0,0,1), bold=True, size_hint_y=None, height=40))
        # Orijinal font boyutu (54sp) korundu, renk yeşil yapıldı (oksijen için)
        self.oxygen_output = Label(font_size='54sp', color=(0.2, 0.6, 0.2, 1), bold=True, size_hint_y=1)
        oxygen_container.add_widget(self.oxygen_output)
        data_layout.add_widget(oxygen_container)
        
        layout.add_widget(data_layout)
        
        # 3. BUTONLAR KISMI: BURADAN TAMAMEN SİLİNDİ
        # (Refresh ve Settings buton kodları çıkarıldı)
        
        self.add_widget(layout)    
        
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def update_display(self):
        """Değişkenleri ekrana basar"""
        self.pulse_output.text = str(self.pulse_value)
        self.oxygen_output.text = f"%{self.oxygen_value}"

    def update_from_main(self, data_string):
        """
        Main.py'dan gelen veriyi işler.
        Format: DATA:NABIZ:SPO2:DURUM
        """
        try:
            data_string = data_string.strip()
            parts = data_string.split(':')
            self.pulse_value = parts[1]
            self.oxygen_value = parts[2]
            self.update_display()
        except Exception as e:
            print(f"Hata: {e}")

    def close_app(self, instance):
        if platform == 'win':
            Window.minimize()
        elif platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            activity.moveTaskToBack(True)