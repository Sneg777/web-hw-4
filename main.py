import mimetypes
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse
import socket
import logging
from threading import Thread, Lock
from datetime import datetime


BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000



class HttpFramework(BaseHTTPRequestHandler):
    def do_GET(self):
        route = (urllib.parse.urlparse(self.path))
        match route.path:
            case '/0:':
                self.send_html('index.html')
            case '/message:':
                self.send_html('message.html')
            case '/error:':
                self.send_html('error.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists() and file.is_file():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        logging.debug(f"Received POST data: {data}")

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()


        self.send_response(302)
        self.send_header('Location', '/contact')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:  # 'br' -> 'rb' для правильного открытия в двоичном режиме
            self.wfile.write(f.read())


    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:  # 'br' -> 'rb' для правильного открытия в двоичном режиме
            self.wfile.write(f.read())





def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    logging.debug(f"Parsed form data: {parse_data}")
    file_lock = Lock()
    try:
        # Парсим данные формы
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        logging.debug(f"Parsed dict: {parse_dict}")

        file_path = 'storage/data.json'

        with file_lock:
            if Path(file_path).exists():
                # Если файл существует, загружаем существующие данные
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        existing_data = json.load(file)
                    except json.JSONDecodeError:
                        logging.error("Error decoding JSON, resetting data.")
                        existing_data = {}
            else:
                existing_data = {}

            # Получаем текущую временную метку
            current_timestamp = str(datetime.now())

            # Добавляем новые данные с временной меткой
            existing_data[current_timestamp] = parse_dict

            # Сохраняем обновлённые данные в файл
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, ensure_ascii=False, indent=4)

        logging.debug(f"Data successfully written to {file_path}")

    except ValueError as err:
        logging.error(f"ValueError during parsing: {err}")
    except OSError as err:
        logging.error(f"OSError during file operations: {err}")

def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()

def run_http_server():
    address = ('0.0.0.0', 3000)
    server = HTTPServer(address, HttpFramework)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    socket_thread = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_thread.start()
    run_http_server()