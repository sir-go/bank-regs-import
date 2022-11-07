import pytest
import requests

from app.conf_test import cfg
from app.cashbox_client import make_fd, CashboxError
from responses import RequestsMock

fake_url = cfg['cashbox']['api_url']
token = cfg['cashbox']['token']
default_place = cfg['cashbox']['default_place']


def test_make_fd(resp: RequestsMock):

    resp.post(fake_url, status=200,
              json={'error': None, 'result': 'some-success-result'})
    result = make_fd(fake_url, token, 'some-order-id',
                     default_place, 69.9, 'some-position')
    assert result == 'some-success-result'

    resp.post(fake_url, status=403,
              json={'error': None, 'result': 'some-success-result'})
    with pytest.raises(requests.HTTPError):
        make_fd(fake_url, token, 'some-order-id',
                default_place, 69.9, 'some-position')

    resp.post(fake_url, status=200,
              json={'error': 'some-error', 'result': ''})
    with pytest.raises(CashboxError):
        make_fd(fake_url, token, 'some-order-id',
                default_place, 69.9, 'some-position')
