
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn, UDPServer, BaseRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import threading
import socket
import json
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
import io

assignment_description = '''
TODO: DELETE THIS DESCRIPTION

Praca domowa nr 4

Twoim celem jest zaimplementowanie prostej aplikacji internetowej. 
Weź następujące pliki z jako podstawę.
Analogicznie do przykładu z notatek, stwórz aplikację internetową z routingiem dla dwóch stron html: index.html i message.html.

Ponadto:
Przetwarzaj podczas działania aplikacji zasoby statyczne: style.css, logo.png;
Zorganizuj pracę z formularzem na stronie message.html;
W przypadku błędu 404 Not Found, zwróć stronę error.html.
Twoja aplikacja działa na porcie 3000

Aby pracować z formularzem, utwórz serwer Socket na porcie 5000. Algorytm jest następujący. 
Użytkownik wprowadza dane do formularza, trafiają one do aplikacji internetowej,
która przesyła je dalej do przetworzenia za pomocą gniazda (protokół UDP), serwera gniazd.
Serwer gniazda tłumaczy otrzymany ciąg bajtów na słownik i zapisuje go w pliku json data.json w folderze przechowywania.

Format pliku data.json jest następujący:

{ "2022-10-29 20:20:58.020261": { "username": "krabaton", "message": "Pierwsza wiadomość" }, 
"2022-10-29 20:21:11.812177": { "username": "krabaton", "message": "Druga wiadomość" } } 

Gdzie kluczem każdej wiadomości jest czas jej otrzymania: datetime.now(). 
Oznacza to, że każda nowa wiadomość z aplikacji internetowej jest dodawana do pliku storage/data.json z czasem jej otrzymania.

Użyj jednego pliku main.py, aby utworzyć aplikację internetową.

Uruchom serwer HTTP i serwer Socket w różnych wątkach.



TODO folder:

Dodatkowe zadanie
Jest to zadanie opcjonalne i można je pominąć w tym zadaniu domowym.

Utwórz plik Dockerfile i uruchom aplikację jako kontener Docker
Korzystając z mechanizmu voluemes, przechowuj dane z storage/data.json poza kontenerem.

WSKAZÓWKA Aby zaimplementować mechanizm volumes, należy sprawdzić istnienie katalogu storage 
i pliku data.json podczas uruchamiania aplikacji. Jeśli ich brakuje, należy je utworzyć.

'''



# HTML templates
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>Index Page</h1>
    <img src="/static/logo.png" alt="Logo">
    <br>
    <a href="/message">Go to Message Page</a>
</body>
</html>
"""

MESSAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>Message Page</h1>
    <form action="/submit" method="post">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" required><br><br>
        <label for="message">Message:</label><br>
        <textarea id="message" name="message" rows="4" cols="50" required></textarea><br><br>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error 404</title>
</head>
<body>
    <h1>Error 404: Page Not Found</h1>
</body>
</html>
"""

def print_logo():
    # Create figure and axis
    fig, ax = plt.subplots()

    # Draw Pac-Man
    pacman = Wedge((0, 0), 1, 30, 330, facecolor='yellow', edgecolor='black')
    ax.add_patch(pacman)

    # Draw eye
    eye = Circle((0.5, 0.5), 0.1, facecolor='black')
    ax.add_patch(eye)

    # Set aspect ratio and limits
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)

    # Remove axes
    ax.axis('off')

    # Add text
    ax.text(1.4, -0.02, "Marina Ultimate Developer", ha='center', fontsize=12, color='white')

    # Set transparent background
    fig.patch.set_alpha(0)

    # Save plot to binary object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)  # Reset buffer position to the start

    # You can now use 'buffer' to access the binary data
    # For example, you can convert it to bytes:
    return buffer.getvalue()


binary_data = print_logo()


#with open('D:/warsztat/programming/Marina/03_web/static/logo.png', 'rb') as f:
#    logo_binary_data = f.read()

# Encode binary data as base64
#png_base64_str = base64.b64encode(logo_binary_data).decode()



# Static files
STATIC_FILES = {
    '/static/style.css': '''
        body { background-color: lightblue; }
        a {
            font-size: 34px; /* Increase hyperlink font size */
            color: blue
        }
    ''',
    '/static/logo.png': binary_data,    
}

#print(png_base64_str)


# Storage directory
STORAGE_DIR = 'D:\warsztat\programming\github\homework_4\storage'
#STORAGE_DIR = '/storage_2'
DATA_FILE = os.path.join(STORAGE_DIR, 'data.json')

print(DATA_FILE)

# Check if storage directory exists, create if not
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

print(STORAGE_DIR)

# Check if data file exists, create if not
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

# Request handler for HTTP server
class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        #print('URL URL {}'.format(url))

        if url.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode())

        elif url.path == '/message':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(MESSAGE_HTML.encode())

        elif url.path in STATIC_FILES:
            self.send_response(200)
            if url.path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif url.path.endswith('.png'):
                self.send_header('Content-type', 'image/png')
            self.end_headers()

            #print(STATIC_FILES[url.path].encode())
            #self.wfile.write(STATIC_FILES[url.path].encode())
               # Check if the requested file exists in STATIC_FILES
            file_data = STATIC_FILES.get(url.path)

            if file_data:
                if isinstance(file_data, bytes):
                    # If the file data is bytes (binary), send it directly
                    self.wfile.write(file_data)
                elif isinstance(file_data, str):
                    # If the file data is a string, encode it to bytes and then send
                    self.wfile.write(file_data.encode())

        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(ERROR_HTML.encode())

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            #print(post_data)
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
        with open(DATA_FILE, 'r+') as f:
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
