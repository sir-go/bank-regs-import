#!/usr/bin/env python3
# coding=utf8
import logging
from functools import wraps
import traceback

from flask import Flask, render_template, request
from flask.logging import default_handler
from jsonrpc.exceptions import JSONRPCDispatchException
from werkzeug.middleware.proxy_fix import ProxyFix
from jsonrpc.backend.flask import api
import exceptions as ex
from cashbox_client import make_fd
from billing_client import BillingService

from conf import cfg

app = Flask(__name__)
app.config.update(cfg['app'])
app.wsgi_app = ProxyFix(app.wsgi_app)
app.url_map.strict_slashes = False


def rpc_error_wrapped(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ex.ParamFormatError as e:
            raise JSONRPCDispatchException(-32051, e.args[0])
        except ex.ApiError:
            raise JSONRPCDispatchException(-32050, 'other api error')
    return wrapped


@app.before_first_request
def setup_logging():
    app.logger = logging.getLogger('regs-ttnet')
    app.logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s\t] : %(message)s')

    app.logger.removeHandler(default_handler)
    # log to console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    app.logger.addHandler(ch)


app.add_url_rule('/api', 'api', api.as_view(), methods=['POST'])


# noinspection PyUnusedLocal
@api.dispatcher.add_method
@rpc_error_wrapped
def make_payment(city_code: str, pay_ext_id: str, pay_timestamp: int, paysum: float, account_id: str,
                 comment: str = None, *args, **kwargs):
    if city_code not in ('tih', 'kor', 'test'):
        raise ex.ParamFormatError('unknown city_code: {}'.format(city_code))

    bsrv = BillingService(api_url=cfg['billing']['api_url'], token=cfg['billing']['token'])

    # noinspection PyBroadException
    try:
        if city_code != 'kor':
            app.logger.debug('city_code != "kor" -> billing.get_account_id({})'.format(account_id))
            account_id = bsrv.get_account_id(account_id)
            app.logger.debug('found account: {}'.format(account_id))
        else:
            account_id = int(account_id)
        bsrv.pay(
            billing=city_code,
            pay_ext_id=pay_ext_id,
            pay_timestamp=pay_timestamp,
            paysum=paysum,
            account_id=account_id,
            pay_method=cfg['billing']['paymethod_code'],
            comment=comment or cfg['billing']['comment'],
            username=cfg['billing']['username'],
            password=cfg['billing']['password']
        )
    except Exception as e:
        app.logger.error(str(request.json))
        app.logger.error(traceback.format_exc())
        raise e


# noinspection PyUnusedLocal
@api.dispatcher.add_method
@rpc_error_wrapped
def make_fiscal(service_code: str, order_id: str, paysum: float,
                place: str = None, *args, **kwargs):
    if service_code not in ('ctv', 'internet'):
        raise ex.ParamFormatError('unknown service_code: {}'.format(service_code))

    if place is None:
        place = cfg['cashbox']['default_place']

    # noinspection PyBroadException
    try:
        pay_params = dict(
            order_id=order_id,
            payments_place=place,
            paysum=paysum,
            position_name='абон. плата за {} (Банк)'.format(
                'КТВ' if service_code == 'ctv' else 'Интернет')
        )

        app.logger.debug(str(pay_params))
        return make_fd(
            api_url=cfg['cashbox']['api_url'],
            token=cfg['cashbox']['token'],
            **pay_params
        )
    except Exception as e:
        app.logger.error(str(request.json))
        app.logger.error(traceback.format_exc())
        raise e


@app.route('/')
def index():
    return render_template("index.html")


# app.debug = True

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8228

    app.run('0.0.0.0', port)
