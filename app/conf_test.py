cfg = {
    'billing': {
        'api_url': "https://billing-url",
        'token': "billing-secret-token",
        'paymethod_code': 2,
        'comment': 'по реестрам из банка',
        'username': "billing-user",
        'password': "billing-password"
    },
    'cashbox': {
        'api_url': "https://cashbox-url",
        'token': "cashbox-secret-token",
        'default_place': 'касса ТелеТайм',
    },
    'app': {
        'DEBUG': True,
        'TESTING': True,
        'SECRET_KEY': "app-secret",
        'TEMPLATES_AUTO_RELOAD': True
    }
}
