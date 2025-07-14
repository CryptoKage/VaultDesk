import os
from hyperliquid.api import API
from dotenv import load_dotenv

load_dotenv()

MASTER_ADDR = os.getenv("MASTER_WALLET_ADDRESS")
agent_key = os.getenv("AGENT_PRIVATE_KEY")

api = API(private_key=agent_key, wallet_address=MASTER_ADDR)
