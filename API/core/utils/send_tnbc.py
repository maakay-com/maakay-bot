import requests
import json

from django.conf import settings

from nacl.encoding import HexEncoder
import nacl.signing
from operator import itemgetter

signing_key = nacl.signing.SigningKey(str.encode(settings.SIGNING_KEY), encoder=nacl.encoding.HexEncoder)
payment_account_number = signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')


def generate_block(balance_lock, transactions, signing_key):
    account_number = signing_key.verify_key.encode(encoder=HexEncoder).decode('utf-8')
    message = {
        'balance_key': balance_lock,
        'txs': sorted(transactions, key=itemgetter('recipient'))
    }
    signature = signing_key.sign(json.dumps(message, separators=(',', ':'), sort_keys=True).encode('utf-8')).signature.hex()
    block = {
        'account_number': account_number,
        'message': message,
        'signature': signature
    }
    return json.dumps(block)


def withdraw_tnbc(recipient, amount, memo):

    bank_config = requests.get(f'http://{settings.BANK_IP}/config?format=json').json()

    balance_lock = requests.get(f"{bank_config['primary_validator']['protocol']}://{bank_config['primary_validator']['ip_address']}:{bank_config['primary_validator']['port'] or 0}/accounts/{payment_account_number}/balance_lock?format=json").json()['balance_lock']

    fee = int(bank_config['default_transaction_fee']) + int(bank_config['primary_validator']['default_transaction_fee'])

    txs = [
        {
            'amount': amount,
            'memo': memo,
            'recipient': recipient,
        },
        {
            'amount': int(bank_config['default_transaction_fee']),
            'fee': 'BANK',
            'recipient': bank_config['account_number'],
        },
        {
            'amount': int(bank_config['primary_validator']['default_transaction_fee']),
            'fee': 'PRIMARY_VALIDATOR',
            'recipient': bank_config['primary_validator']['account_number'],
        }
    ]

    data = generate_block(balance_lock, txs, signing_key)

    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) TNBAccountManager/1.0.0-alpha.43 Chrome/83.0.4103.122 Electron/9.4.0 Safari/537.36',
        'Content-Type': 'application/json',
    }

    r = requests.request("POST", f'http://{settings.BANK_IP}/blocks', headers=headers, data=data)

    return r, fee


def estimate_fee():

    try:
        bank_config = requests.get(f'http://{settings.BANK_IP}/config?format=json').json()

    except:

        return

    fee = int(bank_config['default_transaction_fee']) + int(bank_config['primary_validator']['default_transaction_fee'])

    return fee
