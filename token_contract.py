import json
from web3 import Web3

with open('config.json', 'r') as file:
    config = json.load(file)
infura_key = config["INFURA_KEY"]


def token_contract_abi_builder(name=True, symbol=True, total_supply=True):
    abi = []
    if name:
        abi.append({"inputs": [], "name": "name", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"})
    if symbol:
        abi.append({"inputs": [], "name": "symbol", "outputs": [{"internalType": "string", "name": "", "type": "string"}], "stateMutability": "view", "type": "function"})
    if total_supply:
        abi.append({"inputs": [], "name": "totalSupply", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"})
    return abi


def get_eth_token_details(token_contract_address):
    # Connect to an Ethereum node
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))

    # Token contract ABI (Application Binary Interface)
    # You can find this ABI by looking at the contract's source code or from a site like Etherscan
    token_contract_abi = token_contract_abi_builder(name=True, symbol=True, total_supply=True)

    try:
        # Create a contract object
        token_contract = w3.eth.contract(address=token_contract_address, abi=token_contract_abi)

        # Get token information
        token_name = token_contract.functions.name().call()
        token_symbol = token_contract.functions.symbol().call()
        token_total_supply = token_contract.functions.totalSupply().call()

        return token_name, token_symbol, token_total_supply
    except Exception:
        return None, None, None


def get_bsc_token_details(token_contract_address):
    # Connect to an Ethereum node
    w3 = Web3(Web3.HTTPProvider(f'https://bsc-dataseed1.defibit.io/'))

    # Token contract ABI (Application Binary Interface)
    # You can find this ABI by looking at the contract's source code or from a site like Etherscan
    token_contract_abi = token_contract_abi_builder(name=True, symbol=True, total_supply=True)

    try:
        # Create a contract object
        token_contract = w3.eth.contract(address=token_contract_address, abi=token_contract_abi)

        # Get token information
        token_name = token_contract.functions.name().call()
        token_symbol = token_contract.functions.symbol().call()
        token_total_supply = token_contract.functions.totalSupply().call()

        return token_name, token_symbol, token_total_supply
    except Exception:
        return None, None, None


def query_base_token_info(token_addresses):
    """ Tries to find token information based on input. First successful query is OK! """
    for address in token_addresses:
        token_name, token_symbol, token_total_supply = get_eth_token_details(address)
        if token_name is not None:
            return token_name, token_symbol, token_total_supply

        token_name, token_symbol, token_total_supply = get_bsc_token_details(address)
        if token_name is not None:
            return token_name, token_symbol, token_total_supply

    return None
