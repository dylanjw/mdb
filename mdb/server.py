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
            http_version):

        self.method = method
        self.uri = uri
        self.http_version = http_version


def parse_request(data):
    data = data.decode('utf8')
    lines = data.split('\r\n')
    request_line = lines[0]

    method, uri, http_version = parse_request_start_line(request_line)
    return HTTPRequest(
        method,
        uri,
        http_version,
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


class TCPServer:
    def __init__(
            self,
            host='127.0.0.1',
            port=8888):

        self.host = host
        self.port = port

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure socket to reuse address if socket is stuck
        # in TIME_WAIT state. Prevents "Adress already in use"
        # errors, when  restarting the server.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((self.host, self.port))

        s.listen(5)

        print("Listening at", s.getsockname())

        while True:

            conn, addr = s.accept()
            print("Connected by", addr)
            data = conn.recv(1024)

            response = self.handle_request(data)

            conn.sendall(response.encode('utf8'))
            conn.close()

    def handle_request(self, request):
        return request


def handle_get(request):
    body = [{"message": "Request received!"}]
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


REQUEST_HANDLERS = {
    "GET": handle_get,
    "POST": handle_options,
    "OPTIONS": handle_post,
}


def get_request_handler_by_method(method):
    return REQUEST_HANDLERS.get(method)


class RequestHandler:
    handlers = None

    def __init__(self):
        self.handlers = REQUEST_HANDLERS

    def __call__(self, request):
        request = parse_request(request)
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
    }

    def __init__(self):
        self.request_handler = RequestHandler()

    def handle_request(self, request):
        return self.request_handler(request)
