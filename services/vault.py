from web3 import Web3
import os

INFURA_URL = os.getenv("INFURA_URL")  # e.g. https://mainnet.infura.io/v3/...
VAULT_CONTRACT = os.getenv("VAULT_CONTRACT_ADDRESS")
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "type": "function"},
]

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

def get_token_balance(token_address: str, user_address: str) -> float:
    contract = w3.eth.contract(address=Web3.toChecksumAddress(token_address), abi=ERC20_ABI)
    raw = contract.functions.balanceOf(Web3.toChecksumAddress(user_address)).call()
    decimals = contract.functions.decimals().call()
    return raw / (10 ** decimals)  # human-readable token balance :contentReference[oaicite:6]{index=6}

def get_vault_native_balance(vault_address: str) -> float:
    raw = w3.eth.get_balance(Web3.toChecksumAddress(vault_address))
    return w3.fromWei(raw, "ether")

def get_vault_status(user_address: str) -> dict:
    """
    Get both native and ERC20 balances for the vault.
    """
    return {
        "native": get_vault_native_balance(VAULT_CONTRACT),
        "token": get_token_balance(VAULT_CONTRACT, user_address),
    }
