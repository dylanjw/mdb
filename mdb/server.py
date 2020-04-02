#!/usr/bin/env python3
import socket

from .utils.server import (
    check_server,
    MalformedRequest,
)

from .handlers import (
    RequestHandler,
    DBRequestHandler,
)


class TCPServer:
    def __init__(
            self,
            host='localhost',
            port=8888):

        self.host = host
        self.port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure socket to reuse address if socket is stuck
        # in TIME_WAIT state. Prevents "Adress already in use"
        # errors, when  restarting the server.
        self._socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR, 1)

    def __enter__(self):
        self._bind_socket()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._socket.close()
        if exception_type is not None:
            raise exception_type(exception_value)

    def _bind_socket(self):
        self._socket.bind((self.host, self.port))

    def listen(self):
        self._socket.listen(5)

        for retry in range(5):
            if check_server(self.host, self.port):
                print("Listening at", self._socket.getsockname())
                break
            else:
                raise RuntimeError(
                    "Server failed to set up properly after 5 checks."
                )

        while True:
            conn, addr = self._socket.accept()
            print("Connected by", addr)

            # TODO Require and use a packet length prefix.
            data = conn.recv(1024)

            request = self.handle_request(data)
            if isinstance(request, MalformedRequest):
                conn.close()
            else:
                response = request
                conn.sendall(response.encode('utf8'))
                conn.close()

    def run(self):
        self._bind_socket()
        self.listen()

    def handle_request(self, request):
        return request


class HTTPServer(TCPServer):
    headers = {
        'Server': 'CrudeServer',
        'Content-Type': 'text/json'
    }
    status_code = {
        200: 'OK',
        404: 'Not Found',
        500: 'Server Error'
    }

    def __init__(self):
        super().__init__()
        self.request_handler = RequestHandler()

    def handle_request(self, request):
        return self.request_handler(request)


class DBServer(HTTPServer):
    def __init__(self):
        super().__init__()
        self.request_handler = DBRequestHandler
