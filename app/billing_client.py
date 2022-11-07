import requests


class BillingError(Exception):
    pass


class AccountNotFound(BillingError):
    pass


class PayError(BillingError):
    pass


class PaymentNotFound(PayError):
    pass


class PaymentAlreadyExists(PayError):
    pass


class PaymentCommandError(PayError):
    pass


class DbError(BillingError):
    pass


BillingErrorCodes = {
    -32050: BillingError,
    -32051: AccountNotFound,
    -32052: PaymentNotFound,
    -32053: PaymentAlreadyExists,
    -32054: PaymentCommandError,
    -32055: DbError,
}


def check_rpc_result(rpc_result: dict):
    error = rpc_result.get('error')

    if error is not None:
        if 'code' not in error:
            raise BillingError

        raise BillingErrorCodes.get(error['code'], BillingError)


class BillingService:
    def __init__(self, api_url, token):
        self.__url = api_url
        self.__token = token

    def __call(self, method: str, params: dict):
        r = requests.post(
            url=self.__url,
            headers={
                'Content-Type': 'application/json;charset=utf-8',
                'Authorization': 'Bearer {}'.format(self.__token)
            },
            json={'jsonrpc': '2.0', 'id': 1,
                  'method': method, 'params': params}
        )

        r.raise_for_status()
        return r.json()

    def get_account_id(self, account_ext_id: str) -> int:
        try:
            int(account_ext_id)
        except ValueError:
            raise AccountNotFound

        rpc_result = self.__call(
            method='get_account_info_ext',
            params={
                'billing': 'tih',
                'account_ext_id': account_ext_id
            }
        )

        check_rpc_result(rpc_result)
        rpc_acc_info = rpc_result.get('result')
        if rpc_acc_info is None:
            raise BillingError

        account_id = rpc_acc_info.get('account_id')
        if account_id is None:
            raise AccountNotFound

        return int(account_id)

    def pay(self,
            billing: str,
            pay_ext_id: str,
            pay_timestamp: int,
            paysum: float,
            account_id: int,
            pay_method: int,
            comment: str,
            username: str,
            password: str):
        rpc_result = self.__call(
            method='add_payment',
            params={
                'billing': billing,
                'paysum': paysum,
                'pay_method_code': pay_method,
                'account_id': account_id,
                'pay_ext_id': pay_ext_id,
                'pay_timestamp': pay_timestamp,
                'comment': comment,
                'username': username,
                'password': password
            })

        check_rpc_result(rpc_result)
