from jnius import autoclass, cast
from kivy.clock import mainthread

# --- GLOBAL DEĞİŞKENLER ---
bt_socket = None
bt_output_stream = None
bt_input_stream = None
received_buffer = ""

# Hedef Cihaz Adı (ESP32 Koduyla Aynı)
TARGET_DEVICE_NAME = "Akilli_Bileklik_V6" 

# --- BİLDİRİM FONKSİYONU (İstediğin Gibi) ---
@mainthread
def send_notification(message):
    title = 'Health Warning'
    
    # İSTEĞİN: Sadece ALERT, STATUS ve ! temizlensin.
    message = str(message).replace('!', '').replace('ALERT:', '').replace('STATUS:', '').strip()
    
    if not message:
         message = "ACIL DURUM UYARISI!"

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        
        activity = PythonActivity.mActivity
        nm = cast(NotificationManager, activity.getSystemService(Context.NOTIFICATION_SERVICE))
        
        # Kanal Ayarları (Dokunulmadı - Orijinal)
        channel_id = "pydroid_test_v1"
        
        try:
            NotificationChannel = autoclass('android.app.NotificationChannel')
            if nm.getNotificationChannel(channel_id) is None:
                importance = 4 # High Importance
                channel = NotificationChannel(channel_id, "Test", importance)
                nm.createNotificationChannel(channel)
        except:
            pass 
            
        builder = NotificationBuilder(activity, channel_id)
        builder.setContentTitle(title)
        builder.setContentText(message)
        
        # İkon (Sistem ikonu - Çökmemesi için şart)
        builder.setSmallIcon(17301543) 
        
        builder.setAutoCancel(True)
        
        # Sabit ID
        nm.notify(1, builder.build())
        
    except Exception as e:
        print(f"Hata: {e}")

# --- BAĞLANTI ALTYAPISI (BUNLAR OLMADAN ÇALIŞMAZ) ---
def connect_bluetooth():
    global bt_socket, bt_input_stream
    if bt_socket: return True

    try:
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        UUID = autoclass('java.util.UUID')
        uuid_standard = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
        adapter = BluetoothAdapter.getDefaultAdapter()
        
        if not adapter or not adapter.isEnabled(): return False
        
        paired_devices = adapter.getBondedDevices().toArray()
        target_device = None
        
        for device in paired_devices:
            if device.getName() == TARGET_DEVICE_NAME:
                target_device = device
                break
        
        if target_device:
            bt_socket = target_device.createRfcommSocketToServiceRecord(uuid_standard)
            bt_socket.connect()
            bt_input_stream = bt_socket.getInputStream()
            return True
        else:
            return False
    except Exception as e:
        print(f"BT Bağlantı Hatası: {e}")
        bt_socket = None
        return False

def read_bluetooth_message():
    global bt_input_stream, received_buffer, bt_socket
    
    # Otomatik Bağlanma (Bağlantı koptuğunda geri gelsin diye)
    if bt_socket is None:
        if not connect_bluetooth():
            return "DISCONNECTED"

    if bt_input_stream is None:
        return None

    try:
        buffer = bytearray(1024)
        if bt_input_stream.available() > 0:
            bytes_read = bt_input_stream.read(buffer)
            
            if bytes_read > 0:
                incoming_data = buffer[:bytes_read].decode('utf-8', errors='ignore')
                received_buffer += incoming_data
                
                if '\n' in received_buffer:
                    lines = received_buffer.split('\n')
                    received_buffer = lines[-1]
                    
                    # Öncelik Alarm mesajlarında
                    for line in lines[:-1]:
                         if '!' in line or 'ALERT' in line or 'STATUS' in line:
                             return line.strip()

                    # Normal veri
                    for i in range(len(lines)-2, -1, -1):
                        line = lines[i].strip()
                        if len(line) > 0:
                            return line
        return None
    except Exception as e:
        print(f"Okuma Hatası: {e}")
        bt_socket = None
        return "DISCONNECTED"
