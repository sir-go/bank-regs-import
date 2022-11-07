import pytest
from responses import RequestsMock
from flask import Flask
from app.conf_test import cfg


def test_index(app: Flask):
    index = app.test_client().get('/')
    assert index.status_code == 200
    assert index.content_type == 'text/html; charset=utf-8'
    assert index.get_data(True).startswith('<!DOCTYPE html>')


@pytest.fixture
def _req():
    return {
        'jsonrpc': '2.0', 'method': 'make_payment',
        'params': {
            'city_code': 'tih',
            'pay_ext_id': 'some-pay-ext-id',
            'pay_timestamp': 1111,
            'paysum': 1.1,
            'account_id': '123',
            'comment': 'some-comment'
        }, 'id': 3
    }


def test_make_payment_unknown_city(app: Flask, _req: dict):
    _req['params']['city_code'] = 'unknown-city'
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.status_code == 200
    assert _resp.get_json() == {'error': {
        'code': -32051, 'message': 'unknown city_code: unknown-city'},
        'id': 3, 'jsonrpc': '2.0'}


def test_make_payment_ok(app: Flask, resp: RequestsMock, _req: dict):
    resp.post(cfg['billing']['api_url'], status=200,
              json={'error': None, 'result': {'account_id': 123}})
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.status_code == 200


def test_make_payment_fail(app: Flask, _req: dict):
    _req['params']['account_id'] = 'wtf'
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.get_json() == {
        'error': {'code': -32000, 'data': {
            'args': [], 'message': '', 'type': 'AccountNotFound'
        }, 'message': 'Server error'}, 'id': 3, 'jsonrpc': '2.0'}
