#!/usr/bin/env python3
import socket
import signal
import json

import pytest
import subprocess
import pycurl
from io import BytesIO
import time

from mdb.server import check_server


def wait_for_popen(proc, timeout):
    start = time.time()
    while time.time() < start + timeout:
        if proc.poll() is None:
            time.sleep(0.01)
        else:
            break


def kill_proc_gracefully(proc):
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        wait_for_popen(proc, 13)

    if proc.poll() is None:
        proc.terminate()
        wait_for_popen(proc, 5)

    if proc.poll() is None:
        proc.kill()
        wait_for_popen(proc, 2)


@pytest.fixture
def test_server_process():
    proc = subprocess.Popen(
        ["python", "mdb"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
    )

    for retry in range(10):
        if check_server('localhost', 8888):
            break
        time.sleep(0.1)
    else:
        raise RuntimeError("Failed to connect to server.")

    try:
        yield proc
    finally:
        kill_proc_gracefully(proc)
        output, errors = proc.communicate()
        print(
            "Server Process Exited:\n"
            "stdout:{0}\n\n"
            "stderr:{1}\n\n".format(
                output,
                errors,
            )
        )


@pytest.fixture(autouse=True)
def client_request():
    def inner(uri):
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, 'http://localhost:8888/{}'.format(uri))
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        body = buffer.getvalue()
        return body.decode('utf-8')
    return inner


def test_single_set(test_server_process, client_request):
    set_query = "set?test_key=test_value"
    get_query = "get?test_key"
    response = client_request(set_query)
    print(response)
    response = client_request(get_query)
    assert json.loads(response).get('test_key') == 'test_value'


def test_multiple_set(test_server_process, client_request):
    set_query = "set?test_key1=test_value&test_key2=test_value"
    get_query = "get?test_key2&test_key1"
    response = client_request(set_query)
    print(response)
    response = client_request(get_query)
    assert json.loads(response).get('test_key2') == 'test_value'


def test_bad_request(test_server_process, client_request):
    bad_query = "a;lkdjal;kj;lkj3"
    response = client_request(bad_query)
    assert response == 'Server Error'
