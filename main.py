import tkinter as tk
from tkinter import messagebox
import paho.mqtt.client as mqtt
import json
import ssl
from datetime import datetime
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

# ==========================================
# KONFIGURASI MQTT & DATA
# ==========================================
MQTT_BROKER = "8e5c0bb1547b441d8ff63fd3bde72d67.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "electricwaterjet"
MQTT_PASS = "123456089"
MQTT_TOPIC = "esp32/sensor/data"

MAX_POINTS = 30
data_history = {
    'time': [],
    'rpm': [], 'voltage': [], 'current': [],
    'power': [], 'energy': [], 'temperature': [], 'humidity': []
}

# ==========================================
# TEMA & WARNA MODERN
# ==========================================
BG_MAIN = "#F0F4F8"       # Abu-abu kebiruan terang untuk background
BG_PANEL = "#FFFFFF"      # Putih bersih untuk card/panel
TEXT_MAIN = "#2C3E50"     # Biru dongker untuk teks utama
TEXT_SUB = "#7F8C8D"      # Abu-abu untuk teks sekunder
FONT_MAIN = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_VAL = ("Segoe UI", 14, "bold")

CHART_COLORS = {
    'rpm': '#8E44AD',        # Ungu
    'voltage': '#2980B9',    # Biru
    'current': '#E67E22',    # Oranye
    'power': '#C0392B',      # Merah
    'energy': '#16A085',     # Hijau Tosca
    'temperature': '#D35400',# Oranye Gelap
    'humidity': '#27AE60'    # Hijau
}

# ==========================================
# FUNGSI MQTT
# ==========================================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Terhubung ke Broker MQTT!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Gagal terhubung, kode: {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        now = datetime.now()
        
        data_history['time'].append(now)
        data_history['rpm'].append(payload.get('rpm', 0))
        data_history['voltage'].append(payload.get('voltage', 0))
        data_history['current'].append(payload.get('current', 0))
        data_history['power'].append(payload.get('power', 0))
        data_history['energy'].append(payload.get('energy', 0))
        data_history['temperature'].append(payload.get('temperature', 0))
        data_history['humidity'].append(payload.get('humidity', 0))
        
        if len(data_history['time']) > MAX_POINTS:
            for key in data_history.keys():
                data_history[key].pop(0)
                
    except Exception as e:
        print("Error parsing JSON:", e)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()

# ==========================================
# FUNGSI GUI
# ==========================================
def clear_chart():
    for key in data_history.keys():
        data_history[key].clear()
    print("Grafik dibersihkan!")

def save_csv():
    if not data_history['time']:
        messagebox.showwarning("Peringatan", "Tidak ada data untuk disimpan!")
        return
    
    filename = f"Data_ElectricWaterJet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Waktu', 'RPM', 'Voltage(V)', 'Current(A)', 'Power(W)', 'Energy(Wh)', 'Temperature(C)', 'Humidity(%)'])
            for i in range(len(data_history['time'])):
                writer.writerow([
                    data_history['time'][i].strftime('%H:%M:%S'),
                    data_history['rpm'][i], data_history['voltage'][i],
                    data_history['current'][i], data_history['power'][i],
                    data_history['energy'][i], data_history['temperature'][i],
                    data_history['humidity'][i]
                ])
        messagebox.showinfo("Sukses", f"Data berhasil disimpan ke {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal menyimpan file: {e}")

# ==========================================
# SETUP TKINTER
# ==========================================
root = tk.Tk()
root.title("Dashboard Electric Water Jet")
root.geometry("1280x800")
root.configure(bg=BG_MAIN)

# Header
header_frame = tk.Frame(root, bg="#FFFFFF", height=70)
header_frame.pack(fill=tk.X, side=tk.TOP)
header_frame.pack_propagate(False)
tk.Label(header_frame, text="⚡ Dashboard Electric Water Jet", font=("Segoe UI", 18, "bold"), bg="#FFFFFF", fg=TEXT_MAIN).pack(side=tk.LEFT, padx=25, pady=15)

# Container Utama
main_frame = tk.Frame(root, bg=BG_MAIN)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

charts = {}
labels = {}

def create_chart_panel(parent, row, col, title, data_key, header_title=None):
    # Card Panel
    panel = tk.Frame(parent, bg=BG_PANEL, bd=0, highlightbackground="#E0E6ED", highlightthickness=1)
    panel.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    
    # Header Kategori
    if header_title:
        tk.Label(panel, text=header_title.upper(), font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=TEXT_SUB, anchor="w").pack(fill=tk.X, padx=15, pady=(10,0))
    else:
        tk.Label(panel, text="", bg=BG_PANEL, font=("Segoe UI", 4)).pack(fill=tk.X, pady=(5,0))
        
    # Area Nilai (Value)
    val_frame = tk.Frame(panel, bg=BG_PANEL)
    val_frame.pack(fill=tk.X, padx=15, pady=2)
    tk.Label(val_frame, text=title, font=FONT_TITLE, bg=BG_PANEL, fg=TEXT_MAIN).pack(side=tk.LEFT)
    lbl_val = tk.Label(val_frame, text="0", font=FONT_VAL, bg=BG_PANEL, fg=CHART_COLORS.get(data_key, TEXT_MAIN))
    lbl_val.pack(side=tk.RIGHT)
    
    # Setup Matplotlib
    fig = Figure(figsize=(3.5, 2.2), dpi=100)
    fig.patch.set_facecolor(BG_PANEL)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BG_PANEL)
    
    # Styling Axis
    ax.tick_params(axis='x', colors=TEXT_SUB, labelsize=8)
    ax.tick_params(axis='y', colors=TEXT_SUB, labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E0E6ED')
    ax.spines['bottom'].set_color('#E0E6ED')
    ax.grid(color='#F0F4F8', linestyle='-', linewidth=1)
    
    # Inisialisasi Line (Kosong di awal) untuk pergerakan smooth
    line, = ax.plot([], [], color=CHART_COLORS.get(data_key, "#1f77b4"), linewidth=2.5)
    
    canvas = FigureCanvasTkAgg(fig, master=panel)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    charts[data_key] = (fig, ax, canvas, line)
    labels[data_key] = lbl_val
    return panel

for i in range(4):
    main_frame.columnconfigure(i, weight=1)
for i in range(2):
    main_frame.rowconfigure(i, weight=1)

# Kolom 0: RPM & Tombol
create_chart_panel(main_frame, 0, 0, "Putaran Mesin", "rpm", header_title="RPM Sensor")
btn_frame = tk.Frame(main_frame, bg=BG_MAIN)
btn_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

btn_clear = tk.Button(btn_frame, text="Bersihkan Grafik", font=FONT_MAIN, bg="#E74C3C", fg="white", relief=tk.FLAT, command=clear_chart)
btn_clear.pack(fill=tk.X, pady=10, ipady=8)

btn_csv = tk.Button(btn_frame, text="Simpan Data (CSV)", font=FONT_MAIN, bg="#27AE60", fg="white", relief=tk.FLAT, command=save_csv)
btn_csv.pack(fill=tk.X, pady=5, ipady=8)

# Kolom 1: PZEM (Volt & Ampere)
create_chart_panel(main_frame, 0, 1, "Tegangan (V)", "voltage", header_title="PZEM-017 (Listrik)")
create_chart_panel(main_frame, 1, 1, "Arus (A)", "current")

# Kolom 2: PZEM (Power & Energy)
create_chart_panel(main_frame, 0, 2, "Daya (W)", "power", header_title="PZEM-017 (Daya)")
create_chart_panel(main_frame, 1, 2, "Energi (Wh)", "energy")

# Kolom 3: DHT21
create_chart_panel(main_frame, 0, 3, "Suhu (°C)", "temperature", header_title="DHT21 (Lingkungan)")
create_chart_panel(main_frame, 1, 3, "Kelembapan (%)", "humidity")

# ==========================================
# LOOP UPDATE GRAFIK (SMOOTH ANIMATION)
# ==========================================
def update_gui():
    if data_history['time']:
        time_nums = mdates.date2num(data_history['time'])
        
        for key in charts:
            fig, ax, canvas, line = charts[key]
            
            # Update Nilai Angka
            val = data_history[key][-1]
            labels[key].config(text=f"{val:.0f}" if key == 'rpm' else f"{val:.2f}")
            
            # Update Garis tanpa menghapus Axis (Lebih Smooth)
            line.set_xdata(time_nums)
            line.set_ydata(data_history[key])
            
            # Sesuaikan skala otomatis
            if len(time_nums) > 1:
                ax.set_xlim(time_nums[0], time_nums[-1])
            else:
                ax.set_xlim(time_nums[0], time_nums[0] + 0.0001)
                
            min_y, max_y = min(data_history[key]), max(data_history[key])
            margin = (max_y - min_y) * 0.1 if max_y != min_y else 1
            ax.set_ylim(min_y - margin, max_y + margin)
            
            # Format X-axis ke Jam:Menit:Detik
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            fig.autofmt_xdate(rotation=0, ha='center') 
            
            # Draw idle (rendering jauh lebih halus daripada canvas.draw())
            canvas.draw_idle()
            
    root.after(1000, update_gui)

update_gui()
root.mainloop()
mqtt_client.loop_stop()