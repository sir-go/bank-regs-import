import pytest
import requests

from app.conf_test import cfg
import app.billing_client as b_cl
from responses import RequestsMock

conf = cfg['billing']


@pytest.mark.parametrize('code,error', [
    ({'code': -32050}, b_cl.BillingError),
    ({'code': -32051}, b_cl.AccountNotFound),
    ({'code': -32052}, b_cl.PaymentNotFound),
    ({'code': -32053}, b_cl.PaymentAlreadyExists),
    ({'code': -32054}, b_cl.PaymentCommandError),
    ({'code': -32055}, b_cl.DbError),
    ({}, b_cl.BillingError),
])
def test_check_rpc_result_errors(code, error):
    with pytest.raises(error):
        b_cl.check_rpc_result({'error': code})


def test_check_rpc_result_none():
    try:
        assert b_cl.check_rpc_result({'some': 'answer'}) is None
    except Exception as e:
        assert e


def test_get_account_id(resp: RequestsMock):
    s = b_cl.BillingService(conf['api_url'], conf['token'])
    with pytest.raises(b_cl.AccountNotFound):
        s.get_account_id('some-ext-id')
        s.get_account_id('')

    resp.post(conf['api_url'], status=503,
              json={'error': None, 'result': {'account_id': 321}})
    with pytest.raises(requests.HTTPError):
        s.get_account_id('123')

    resp.post(conf['api_url'], status=200,
              json={'error': None, 'result': {'account_id': 321}})
    assert s.get_account_id('123') == 321

    resp.post(conf['api_url'], status=200, json={'error': None})
    with pytest.raises(b_cl.BillingError):
        s.get_account_id('123')

    resp.post(conf['api_url'], status=200,
              json={'error': None, 'result': {'not': 'account'}})
    with pytest.raises(b_cl.AccountNotFound):
        s.get_account_id('123')


def test_pay(resp: RequestsMock):
    s = b_cl.BillingService(conf['api_url'], conf['token'])
    resp.post(conf['api_url'], status=503, json={})
    with pytest.raises(requests.HTTPError):
        s.pay('b', '', 0, 0.0, 0, 0, '', '', '')
