#!/usr/bin/env python3
#
from toolz import (
    merge,
    assoc,
    keyfilter,
)
import json
from .utils import (
    mutate_merge,
)
from .utils.server import (
    Response,
    parse_request,
    MalformedRequest,
)
from .db import (
    memdb,
)


def default_handle_get(request):
    body = [{"received request": request.raw_request.decode('utf8')}]
    body = json.dumps(body)
    response = Response(
        status=200,
        body=body,
    )
    return response.to_string()


def default_handle_options(request):
    response = Response(
        status=200,
        extra_headers={'Allow': 'OPTIONS, GET'},
        body=""
    )
    return response.to_string()


def default_handle_post(request):
    raise NotImplementedError


DEFAULT_REQUEST_HANDLERS = {
    "GET": default_handle_get,
    "POST": default_handle_options,
    "OPTIONS": default_handle_post,
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


def parse_uri(request):
    uri = request.uri
    db_method, query_string = uri.split("?")
    query_parameters = query_string.split("&")

    if db_method not in ['/set', '/get']:
        raise ValueError(f"Invalid db method: {db_method}")

    return db_method, query_parameters


def parse_set_query_params(query_params):
    values = dict()
    for param in query_params:
        key, value = param.split("=")
        values = assoc(values, key, value)
    return values


def handle_db_get(request):
    try:
        db_method, query_params = parse_uri(request)
        if db_method == '/get':
            response_data = keyfilter(
                lambda key: key in query_params,
                memdb,
            )
        if db_method == '/set':
            values = parse_set_query_params(query_params)
            mutate_merge(memdb, values)
            response_data = ["success"]

        body = json.dumps(response_data)

        response = Response(
            status=200,
            body=body,
        )
    except ValueError as e:
        response = Response(
            status=500,
            body="Server Error",
        )
        print(e)

    return response.to_string()


DBRequestHandler = RequestHandler({'GET': handle_db_get})
