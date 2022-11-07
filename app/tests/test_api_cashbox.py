import pytest
from responses import RequestsMock
from flask import Flask
from app.conf_test import cfg


@pytest.fixture
def _req():
    return {
        'jsonrpc': '2.0', 'method': 'make_fiscal',
        'params': {
            'service_code': 'internet',
            'order_id': 'some-order-id',
            'place': 'some-place',
            'paysum': 1.1,
        }, 'id': 5
    }


def test_make_fiscal_unknown_service(app: Flask, _req: dict):
    _req['params']['service_code'] = 'unknown-service'
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.status_code == 200
    assert _resp.get_json() == {'error': {
        'code': -32051, 'message': 'unknown service_code: unknown-service'},
        'id': 5, 'jsonrpc': '2.0'}


def test_make_fiscal_ok(app: Flask, resp: RequestsMock, _req: dict):
    resp.post(cfg['cashbox']['api_url'], status=200,
              json={'error': None, 'result': 'some-fiscal-result'})
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.status_code == 200
    assert _resp.get_json() == {
        'id': 5, 'jsonrpc': '2.0', 'result': 'some-fiscal-result'}


def test_make_fiscal_fail(app: Flask, resp: RequestsMock, _req: dict):
    # answer without JSON
    resp.post(cfg['cashbox']['api_url'], status=200)
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.get_json().get('error').get('code') == -32000

    # answer with error
    resp.post(cfg['cashbox']['api_url'], status=200,
              json={'error': 'some-error'})
    _resp = app.test_client().post('/api', json=_req)
    assert _resp.get_json() == {
        'error': {'code': -32000,
                  'data': {
                      'args': ['some-error'],
                      'message': 'some-error',
                      'type': 'CashboxError'
                  }, 'message': 'Server error'}, 'id': 5, 'jsonrpc': '2.0'}
