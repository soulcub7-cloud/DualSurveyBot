from pathlib import Path
from dotenv import dotenv_values

env_path = Path(__file__).parent / ".env"

print("Путь к .env:", env_path)
print("Файл существует:", env_path.exists())

config = dotenv_values(env_path)

print(config)

BOT_TOKEN = config.get("BOT_TOKEN")
ADMIN_ID = int(config.get("ADMIN_ID", 0))
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPECIALIST_ID = int(os.getenv("SPECIALIST_ID", "0"))