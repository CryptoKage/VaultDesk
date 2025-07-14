import os
from dotenv import load_dotenv

load_dotenv()

SETTINGS = {
    "env": os.getenv("ENVIRONMENT", "dev"),
    "agent_key": os.getenv("AGENT_PRIVATE_KEY"),
    "master_address": os.getenv("MASTER_WALLET_ADDRESS"),
    "leverage": float(os.getenv("LEVERAGE", 1)),
    "debug": os.getenv("DEBUG_MODE", "false").lower() == "true"
}

if not SETTINGS["agent_key"] or not SETTINGS["master_address"]:
    raise EnvironmentError("Missing AGENT_PRIVATE_KEY or MASTER_WALLET_ADDRESS in .env")
