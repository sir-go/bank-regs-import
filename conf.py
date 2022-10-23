# coding=utf8

cfg = {
    'billing': {
        'api_url': "${BILLING_API_URL}",
        'token': "${BILLING_API_TOKEN}",
        'paymethod_code': 2,
        'comment': 'по реестрам из банка',
        'username': "${BILLING_USERNAME}",
        'password': "${BILLING_PASSWORD}"
    },
    'cashbox': {
        'api_url': "${CASHBOX_API_URL}",
        'token': "${CASHBOX_API_TOKEN}",
        'default_place': 'касса ТелеТайм',
    },
    'app': {
        'DEBUG': True,
        'TESTING': False,
        'SECRET_KEY': "${APP_SECRET}",
        'TEMPLATES_AUTO_RELOAD': True
    }
}
