from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn, UDPServer, BaseRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import threading
import socket
import json
import os

# Storage directory
all_files = "./"

storage_dir = './storage'
data_file = os.path.join(storage_dir, 'data.json')
print(data_file)
# Check if storage directory exists, create if not
if not os.path.exists(storage_dir):
    os.makedirs(storage_dir)
storage_dir = './storage'
print(storage_dir)

# Check if data file exists, create if not
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        json.dump({}, f)

# Request handler for HTTP server
# Request handler for HTTP server
class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)

        if url.path == '/':
            filename = os.path.join(all_files, 'index.html')
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(filename, 'rb') as f:
                self.wfile.write(f.read())

        elif url.path == '/message':
            filename = os.path.join(all_files, 'message.html')
            if os.path.exists(filename):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(filename, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
        
        elif url.path.endswith('.css'):
            filename = os.path.join(all_files, url.path.lstrip('/'))
            if os.path.exists(filename):
                self.send_response(200)
                self.send_header('Content-type', 'text/css')
                self.end_headers()
                with open(filename, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
        
        elif url.path.endswith('.png'):
            filename = os.path.join(all_files, url.path.lstrip('/'))
            if os.path.exists(filename):
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                with open(filename, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            parsed_data = parse_qs(post_data.decode())
            username = parsed_data['username'][0]
            message = parsed_data['message'][0]

            # Send data to socket server
            try:
                udp_client.sendto(json.dumps({"username": username, "message": message}).encode(), ('localhost', 5000))
            except Exception as e:
                print('error {}'.format(e))                     

            # Redirect to message page
            self.send_response(303)
            self.send_header('Location', '/message')
            self.end_headers()

# Request handler for UDP server
class UDPRequestHandler(BaseRequestHandler):
    def handle(self):
        data, _ = self.request
        data_dict = json.loads(data.decode())
        timestamp = str(datetime.now())
        with open(data_file, 'r+') as f:
            stored_data = json.load(f)
            stored_data[timestamp] = data_dict
            f.seek(0)
            json.dump(stored_data, f)

# Multithreaded HTTP server
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

# Multithreaded UDP server
class ThreadedUDPServer(ThreadingMixIn, UDPServer):
    pass

# Start UDP server in a separate thread
def start_udp_server():
    udp_server.serve_forever()

# HTTP server
http_server = ThreadedHTTPServer(('localhost', 3000), HTTPRequestHandler)

# UDP server
udp_server = ThreadedUDPServer(('localhost', 5000), UDPRequestHandler)

# Start UDP server in a separate thread
udp_thread = threading.Thread(target=start_udp_server)
udp_thread.start()

# UDP client
udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Start HTTP server
http_server.serve_forever()
