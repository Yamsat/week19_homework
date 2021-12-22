# Import dependencies
import subprocess
import json
from dotenv import load_dotenv
import os

# Load and set environment variables
load_dotenv()
mnemonic=os.getenv("mnemonic")

# Import constants.py and necessary functions from bit and web3
import constants
from web3 import Web3
from web3.middleware import geth_poa_middleware
from bit import PrivateKeyTestnet, network
from eth_account import Account

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
 
# Create a function called `derive_wallets`
def derive_wallets(mnemonic, coin, numderive):
    command = f'php derive -g --mnemonic="{mnemonic}" --cols=path,address,privkey,pubkey --coin={coin} --numderive={numderive} --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.
coins = {}
crypto = [constants.ETH, constants.BTCTEST]
for c in crypto:
    coins[c] = derive_wallets(mnemonic, c, 3)

# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    if coin == 'eth':
        return Account.privateKeyToAccount(priv_key)
    elif coin == 'btc-test':
        return PrivateKeyTestnet(priv_key)
    
# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, to, amount):
    if coin == 'eth':
        gasEstimate = w3.eth.estimateGas({"from": account.address, "to": to, "value": amount})
        return {
        "from": account.address,
        "to": to,
        "value": amount,
        "gasPrice": w3.eth.gasPrice,
        "gas": gasEstimate,
        "nonce": w3.eth.getTransactionCount(account.address),
        }
    elif coin == 'btc-test':
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, 'btc')])

# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, to, amount):
    if coin == 'eth':
        raw_tx = create_tx(coin, account, to, amount)
        signed_tx = account.sign_transaction(raw_tx)
        return w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    elif coin == 'btc-test':
        raw_tx = create_tx(coin, account, to, amount)
        signed_tx = account.sign_transaction(raw_tx)
        return network.NetworkAPI.broadcast_tx_testnet(signed_tx)

# Transfer BTC0.0001 from one account to another
btc_test = constants.BTCTEST
priv = coins['btc-test'][0]['privkey']
account = priv_key_to_account(btc_test, priv)

to = 'mhVeFuDDLfqNBcn8ZkWYVCX7te1Nieh8my'
send_tx(btc_test, account, to, 0.0001)

# Transfer ETH100000000 from one account to another
eth = constants.ETH
priv = coins['eth'][0]['privkey']
account = priv_key_to_account(eth, priv)

to = '0xFb86Ad9D772cfc495B04C864307Ef289c14089Cc'
send_tx(eth, account, to, 1000000000)

w3.eth.getTransactionReceipt('0xe9903c388cd4f7bf7bae6cc447a165fae224cb456ea6627aafa87fa1552eb192')
