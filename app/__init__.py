import logging
from functools import wraps
import traceback

from flask import Flask, render_template, request
from flask.logging import default_handler
from jsonrpc.exceptions import JSONRPCDispatchException
from werkzeug.middleware.proxy_fix import ProxyFix
from jsonrpc.backend.flask import api
from app.exceptions import ApiError, ParamFormatError
from app.cashbox_client import make_fd
from app.billing_client import BillingService


def create_app(conf: dict) -> Flask:

    def rpc_error_wrapped(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ParamFormatError as e:
                raise JSONRPCDispatchException(-32051, e.args[0])
            except ApiError:
                raise JSONRPCDispatchException(-32050, 'other api error')
        return wrapped

    _app = Flask(__name__, instance_relative_config=True)
    _app.config.update(conf['app'])
    _app.wsgi_app = ProxyFix(_app.wsgi_app)
    _app.url_map.strict_slashes = False

    if not _app.testing:
        _app.logger = logging.getLogger('regs-ttnet')
        _app.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s\t] : %(message)s')

        _app.logger.removeHandler(default_handler)
        # log to console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        _app.logger.addHandler(ch)

    _app.add_url_rule('/api', 'api', api.as_view(), methods=['POST'])

    @api.dispatcher.add_method
    @rpc_error_wrapped
    def make_payment(city_code: str, pay_ext_id: str, pay_timestamp: int,
                     paysum: float, account_id: str,
                     comment: str = None, *args, **kwargs):
        if city_code not in ('tih', 'kor', 'test'):
            raise ParamFormatError(f'unknown city_code: {city_code}')

        bsrv = BillingService(api_url=conf['billing']['api_url'],
                              token=conf['billing']['token'])

        # noinspection PyBroadException
        try:
            if city_code != 'kor':
                _app.logger.debug(f'city_code != "kor" -> '
                                  f'billing.get_account_id({account_id})')
                account_id = bsrv.get_account_id(account_id)
                _app.logger.debug(f'found account: {account_id}')
            else:
                account_id = int(account_id)
            bsrv.pay(
                billing=city_code,
                pay_ext_id=pay_ext_id,
                pay_timestamp=pay_timestamp,
                paysum=paysum,
                account_id=account_id,
                pay_method=conf['billing']['paymethod_code'],
                comment=comment or conf['billing']['comment'],
                username=conf['billing']['username'],
                password=conf['billing']['password']
            )
        except Exception as e:
            _app.logger.error(str(request.json))
            _app.logger.error(traceback.format_exc())
            raise e

    # noinspection PyUnusedLocal
    @api.dispatcher.add_method
    @rpc_error_wrapped
    def make_fiscal(service_code: str, order_id: str, paysum: float,
                    place: str = None, *args, **kwargs):
        if service_code not in ('ctv', 'internet'):
            raise ParamFormatError(f'unknown service_code: {service_code}')

        if place is None:
            place = conf['cashbox']['default_place']

        # noinspection PyBroadException
        try:
            pay_params = dict(
                order_id=order_id,
                payments_place=place,
                paysum=paysum,
                position_name='абон. плата за {} (Банк)'.format(
                    'КТВ' if service_code == 'ctv' else 'Интернет')
            )

            _app.logger.debug(str(pay_params))
            return make_fd(
                api_url=conf['cashbox']['api_url'],
                token=conf['cashbox']['token'],
                **pay_params
            )
        except Exception as e:
            _app.logger.error(str(request.json))
            _app.logger.error(traceback.format_exc())
            raise e

    @_app.route('/')
    def index():
        return render_template("index.html")

    return _app


def prod():
    from app.conf import cfg
    return create_app(cfg)
