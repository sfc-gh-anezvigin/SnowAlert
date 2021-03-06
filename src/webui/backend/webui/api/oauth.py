from os import environ
from urllib.parse import urlencode

from requests.auth import HTTPBasicAuth
import requests

from flask import Blueprint, request, jsonify
import logbook

logger = logbook.Logger(__name__)

oauth_api = Blueprint('oauth', __name__)

OAUTH_CONNECTION_ROLE = environ.get('OAUTH_CONNECTION_ROLE', None)
if OAUTH_CONNECTION_ROLE:
    scope_role = f' session:role:{OAUTH_CONNECTION_ROLE.upper()}'
else:
    scope_role = ''


PROTOCOL = environ.get('SNOWFLAKE_PROTOCOL', 'https')
PORT = environ.get('SNOWFLAKE_PORT', '443')
URL_PREFIX = f'{PROTOCOL}://{{account}}.snowflakecomputing.com' + (
    '' if PORT == '443' else f':{PORT}'
)


@oauth_api.route('/redirect', methods=['POST'])
def oauth_redirect():
    json = request.get_json()
    account = json.get('account')
    returnHref = json.get('returnHref')

    OAUTH_CLIENT_ID = environ.get(
        f'OAUTH_CLIENT_{account.partition(".")[0].upper()}', ''
    )

    return jsonify(
        url=f"{URL_PREFIX}/oauth/authorize?".format(account=account)
        + urlencode(
            {
                'client_id': OAUTH_CLIENT_ID,
                'response_type': 'code',
                'scope': f'refresh_token{scope_role}',
                'redirect_uri': returnHref,
            }
        )
    )


@oauth_api.route('/return', methods=['POST'])
def oauth_return():
    json = request.get_json()
    code = json.get('code')
    account = json.get('account')
    redirect_uri = json.get('redirectUri')

    OAUTH_CLIENT_ID = environ.get(
        f'OAUTH_CLIENT_{account.partition(".")[0].upper()}', ''
    )
    OAUTH_SECRET_ID = environ.get(
        f'OAUTH_SECRET_{account.partition(".")[0].upper()}', ''
    )

    response = requests.post(
        f"{URL_PREFIX}/oauth/token-request".format(account=account),
        auth=HTTPBasicAuth(OAUTH_CLIENT_ID, OAUTH_SECRET_ID),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code,
        },
    )

    return jsonify(tokens=response.json())
