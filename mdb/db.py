#!/usr/bin/env python3
#

import json
from toolz import (
    assoc,
    merge,
    keyfilter,
)
from mdb.server import (
    Response,
    HTTPServer,
    RequestHandler,
)

ALLOWED_DB_METHODS = ["/get", "/set"]
GLOBAL_DB = {}


def mutate_merge(*dicts):
    for d in dicts[1:]:
        dicts[0].update(d)


def parse_uri(request):
    uri = request.uri
    db_method, query_string = uri.split("?")
    query_parameters = query_string.split("&")

    if db_method not in ALLOWED_DB_METHODS:
        raise ValueError(f"Invalid db method: {db_method}")

    return db_method, query_parameters


def parse_set_query_params(query_params):
    values = dict()
    for param in query_params:
        key, value = param.split("=")
        values = assoc(values, key, value)
    return values


def handle_get(request):
    try:
        db_method, query_params = parse_uri(request)
        if db_method == '/get':
            response_data = keyfilter(
                lambda key: key in query_params,
                GLOBAL_DB,
            )
        if db_method == '/set':
            values = parse_set_query_params(query_params)
            mutate_merge(GLOBAL_DB, values)
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


class DBServer(HTTPServer):
    def __init__(self):
        super().__init__()
        self.request_handler = RequestHandler({'GET': handle_get})
