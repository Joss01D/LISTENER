from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8000  # Render asigna su propio puerto, lo sobreescribiremos abajo

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parseamos la URL y los parámetros
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        
        # Aquí tu variable 'c' vendría del query string
        c_value = query.get('c', [''])[0]
        print(f"Recibido: {c_value}")  # Esto se verá en los logs de Render
        
        # Respuesta HTTP
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Recibido: {c_value}".encode())

# Render asigna el puerto mediante variable de entorno
import os
PORT = int(os.environ.get("PORT", 8000))

with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"Servidor corriendo en puerto {PORT}")
    httpd.serve_forever()
