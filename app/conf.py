cfg = {
    'billing': {                            # billing access settings
        'api_url': "${BILLING_API_URL}",    # UTM5 api url
        'token': "${BILLING_API_TOKEN}",    # UTM5 api token
        'paymethod_code': 2,                # 'bank transfer'
        'comment': 'по реестрам из банка',  # default comment
        'username': "${BILLING_USERNAME}",  # UTM5 system account name
        'password': "${BILLING_PASSWORD}"   # UTM5 system account password
    },
    'cashbox': {                            # TOS terminal access settings
        'api_url': "${CASHBOX_API_URL}",    # TOS api url
        'token': "${CASHBOX_API_TOKEN}",    # TOS api token
        'default_place': 'касса ТелеТайм',  # default payment place
    },
    'app': {                                # app settings
        'DEBUG': False,                     # run in debug mode ?
        'TESTING': False,                   # is it test run ?
        'SECRET_KEY': "${APP_SECRET}",      # web app secret kay
        'TEMPLATES_AUTO_RELOAD': True       # do reload templates if changed ?
    }
}
