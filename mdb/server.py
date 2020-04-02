#!/usr/bin/env python3
import socket
from toolz import merge
import json


class HTTPRequest:
    method = None
    uri = None
    http_version = None
    headers = {}

    def __init__(
            self,
            method,
            uri,
            http_version,
            body,
            raw_request):

        self.method = method
        self.uri = uri
        self.http_version = http_version
        self.body = body
        self.raw_request = raw_request


class MalformedRequest(HTTPRequest):
    def __init__(self):
        pass


def parse_request(raw_request):
    data = raw_request.decode('utf8')
    lines = data.split('\r\n')
    request_line = lines[0]
    body = ""
    if len(lines) >= 2:
        body = lines[1]

    method, uri, http_version = parse_request_start_line(request_line)
    return HTTPRequest(
        method,
        uri,
        http_version,
        body,
        raw_request,
    )


def parse_request_start_line(request_line):
    words = request_line.split(' ')

    method = words[0]
    uri = words[1]

    if len(words) > 2:
        http_version = words[2]
    else:
        http_version = '1.1'

    return method, uri, http_version


def check_server(host, port):
    try:
        s = socket.socket()
        s.connect((host, port))
        return True
    except socket.error:
        return False
    finally:
        s.close()


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
                raise RuntimeError("Server failed to set up properly after 5 checks.")

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


def handle_get(request):
    body = [{"received request": request.raw_request.decode('utf8')}]
    body = json.dumps(body)
    response = Response(
        status=200,
        body=body,
    )
    return response.to_string()


def handle_options(request):
    response = Response(
        status=200,
        extra_headers={'Allow': 'OPTIONS, GET'},
        body=""
    )
    return response.to_string()


def handle_post(request):
    raise NotImplementedError


DEFAULT_REQUEST_HANDLERS = {
    "GET": handle_get,
    "POST": handle_options,
    "OPTIONS": handle_post,
}


class RequestHandler:
    handlers = None

    def __init__(self, handlers=None):
        self.handlers = DEFAULT_REQUEST_HANDLERS

        if handlers is not None:
            self.handlers = merge(self.handlers, handlers)

    def __call__(self, request):
        try:
            request = parse_request(request)
        except IndexError:
            print("Received non-http formed packet")
            return MalformedRequest()
        try:
            handler = self.handlers[request.method]
        except IndexError:
            raise NotImplementedError(
                "Response handler not implemented for {}".format(
                    request.method
                )
            )
        return handler(request)


STATUS_CODES = {
    200: 'OK',
    404: 'Not Found',
    500: 'Server Error'
}


class Response:
    status_codes = None
    status = None
    extra_headers = None
    default_headers = {
        'Server': 'CrudeServer',
        'Content-Type': 'text/html'
    }

    response_line_format = "HTTP/1.1 {} {}\r\n"

    def __init__(self, status=200, extra_headers=None, body=None):
        self.extra_headers = extra_headers
        self.body = body
        self.status_codes = STATUS_CODES
        if status in self.status_codes.keys():
            self.status = status
        else:
            ValueError("Instantiated with invalid status code")

    def format_response_line(self):
        return self.response_line_format.format(
            self.status,
            self.status_codes[self.status]
        )

    def format_headers(self):
        _headers = self.default_headers

        if self.extra_headers:
            _headers = merge(self.extra_headers)

        formatted_headers = ""

        for h, h_value in _headers.items():
            formatted_headers += "{}: {}\r\n".format(h, h_value)

        return formatted_headers

    def to_string(self):
        return "{}{}{}{}".format(
            self.format_response_line(),
            self.format_headers(),
            "\r\n",
            self.body,
        )


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
