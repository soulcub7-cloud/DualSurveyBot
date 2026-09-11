import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SPECIALIST_ID = int(os.getenv("SPECIALIST_ID", "0"))
LMS_API_URL = os.getenv("LMS_API_URL", "").rstrip("/")
LMS_BOT_INTEGRATION_TOKEN = os.getenv("LMS_BOT_INTEGRATION_TOKEN", "")
