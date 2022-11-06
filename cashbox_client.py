import requests


class CashboxError(Exception):
    pass


def make_fd(
        api_url: str,
        token: str,
        order_id: str,
        payments_place: str,
        paysum: float,
        position_name: str) -> int:
    print(order_id, payments_place, paysum, position_name)
    r = requests.post(
        url=api_url,
        headers={'Content-Type': 'application/json;charset=utf-8'},
        json={
            'token': token,
            'method': 'digital_pay',
            'params': {
                'order_id': order_id,
                'payments_place': payments_place,
                'paysum': paysum,
                'position_name': position_name,
                'dont_wait_ofd': True
            }
        }
    )

    r.raise_for_status()
    json_answer = r.json()

    fiscal_error = json_answer.get('error')
    fiscal_result = json_answer.get('result')

    if fiscal_error is not None:
        raise CashboxError(fiscal_error)

    return fiscal_result
