import socket
from toolz import (
    merge,
)


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


def parse_request_start_line(request_line):
    words = request_line.split(' ')

    method = words[0]
    uri = words[1]

    if len(words) > 2:
        http_version = words[2]
    else:
        http_version = '1.1'

    return method, uri, http_version


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


def check_server(host, port):
    try:
        s = socket.socket()
        s.connect((host, port))
        return True
    except socket.error:
        return False
    finally:
        s.close()


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
