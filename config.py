import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PARENT_FOLDER_ID = os.getenv("PARENT_FOLDER_ID")

SERVICE_ACCOUNT_FILE = "credentials/service_account.json"